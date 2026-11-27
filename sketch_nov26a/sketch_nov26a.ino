#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <LiquidCrystal_I2C.h>

// ---------- BLE UUIDs ----------
#define SERVICE_UUID "377aa64e-3265-4da3-a529-7d4f06c0a7f0"
#define LED_UUID     "f5c287f5-febb-47bd-be3b-c3a4955bc07b"
#define CRED_UUID    "6e1d7a52-3f0b-4c7e-9a41-5b8d2c0f1e93"
#define RESULT_UUID  "a3c4f8d1-72e5-4b19-8d6a-0c9e4f2b7a15"
#define EVENT_UUID "c2b7e9a4-5d13-4f86-b0a2-7e1d9c3f4a68"

// ---------- Hardware ----------
LiquidCrystal_I2C lcd(0x27, 16, 2);
const int BUZZER_PIN = 4;

const int ROWS[4]    = {14, 27, 26, 25};
const int COLUMNS[4] = {33, 32, 19, 18};

const char KEYS[4][4] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

// ---------- Servo ----------
const int SERVO_PIN     = 2;
const int SERVO_CHANNEL = 4;

const int SERVO_CW_US   = 2000;   // reversed from before; use 1000 for the other direction
const int SERVO_STOP_US = 1500;   // adjust the servo's trim screw if it creeps
const int SPIN_TIME_MS  = 1000;   // time for one full turn, tune this

uint32_t servoDuty(int microseconds) {
  return (uint32_t)microseconds * 16383UL / 20000UL;   // 14-bit, 50 Hz
}

void spinServoOnce() {
  ledcWrite(SERVO_PIN, servoDuty(SERVO_CW_US));
  delay(SPIN_TIME_MS);
  ledcWrite(SERVO_PIN, servoDuty(SERVO_STOP_US));
}

const unsigned long OPEN_LIMIT_MS = 10000;   // 10 s for testing, raise it later
unsigned long openedAt = 0;
bool alarmActive = false;
unsigned long lastAlarmBeep = 0;

// ---------- BLE state ----------
BLECharacteristic *pLedStateChar;
BLECharacteristic *pCredChar;
BLECharacteristic *pResultChar;
BLECharacteristic *pEventChar;

bool waitingResult = false;
unsigned long submitTime = 0;
volatile uint8_t resultCode = 0;   // written by the BLE task, read by loop()

class ResultCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *c) override {
    if (c->getLength() >= 1) resultCode = *c->getData();
  }
};

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *s) override {}
  void onDisconnect(BLEServer *s) override {
    BLEDevice::startAdvertising();   // keep advertising so the Pi can reconnect
  }
};

// ---------- Input state ----------
const int MIN_LEN = 4;
const int MAX_LEN = 6;

enum Phase { PHASE_PIN, PHASE_PASSCODE, PHASE_OPEN };
Phase phase = PHASE_PIN;

String input = "";
String pin = "";
String passcode = "";
char lastKey = 0;

// ---------- Buzzer ----------
void playTone(int frequency, int duration) {
  tone(BUZZER_PIN, frequency, duration);
  delay(duration);
  noTone(BUZZER_PIN);
  yield();
}

// ---------- Keypad ----------
void setupNumpad() {
  for (int c = 0; c < 4; c++) {
    pinMode(COLUMNS[c], OUTPUT);
    digitalWrite(COLUMNS[c], LOW);
  }
  for (int r = 0; r < 4; r++) {
    pinMode(ROWS[r], INPUT_PULLDOWN);
  }
}

char readNumpad() {
  for (int c = 0; c < 4; c++) {
    digitalWrite(COLUMNS[c], HIGH);
    delayMicroseconds(50);
    char key = 0;
    for (int r = 0; r < 4; r++) {
      if (digitalRead(ROWS[r]) == HIGH) {
        key = KEYS[r][c];
        break;
      }
    }
    digitalWrite(COLUMNS[c], LOW);
    if (key) return key;
  }
  return 0;
}

// ---------- LCD ----------
void showBottom(const char *text) {
  lcd.setCursor(0, 1);
  lcd.print(text);
  for (int i = strlen(text); i < 16; i++) lcd.print(' ');   // wipe leftovers
}

void showHint() {
  showBottom("*=clear #=ok");
}

void renderInput() {
  int col = (phase == PHASE_PIN) ? 4 : 9;      // length of "PIN:" / "PASSCODE:"
  lcd.setCursor(col, 0);
  for (int i = col; i < 16; i++) lcd.print(' ');
  lcd.setCursor(col, 0);

  if (phase == PHASE_PIN) {
    lcd.print(input);
  } else {
    for (unsigned int i = 0; i < input.length(); i++) lcd.print('*');
  }
}

void showPrompt() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(phase == PHASE_PIN ? "PIN:" : "PASSCODE:");
  renderInput();
  showHint();
}

void resetForm() {
  alarmActive = false;
  pin = "";
  passcode = "";
  input = "";
  phase = PHASE_PIN;
  showPrompt();
}

// ---------- Login flow ----------
void submit() {
  String payload = pin + ":" + passcode;
  resultCode = 0;
  waitingResult = true;
  submitTime = millis();
  pCredChar->setValue((uint8_t *)payload.c_str(), payload.length());
  pCredChar->notify();
  showBottom("Checking...");
}

void sendEvent(const char *name) {
  pEventChar->setValue((uint8_t *)name, strlen(name));
  pEventChar->notify();
}

void onAccessGranted() {
  phase = PHASE_OPEN;
  openedAt = millis();
  alarmActive = false;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Close safe with");   // 16 columns only, so split over two rows
  lcd.setCursor(0, 1);
  lcd.print("'D'");

  playTone(1500, 150);
  playTone(2000, 250);
  spinServoOnce();
  sendEvent("opened");
}

void checkResult() {
  if (!waitingResult) return;

  uint8_t r = resultCode;
  if (r == 1 || r == 2) {
    waitingResult = false;
    resultCode = 0;
    if (r == 1) {
      onAccessGranted();          // stays on the "Close safe" screen until D
    } else {
      showBottom("Access denied");
      playTone(200, 100);
      playTone(200, 100);
      delay(1500);
      resetForm();
    }
  } else if (millis() - submitTime > 10000) {
    waitingResult = false;
    showBottom("No response");
    playTone(200, 400);
    delay(1500);
    resetForm();
  }
}

void checkOpenTimeout() {
  if (phase != PHASE_OPEN) return;

  // First time the limit is exceeded: change the screen
  if (!alarmActive && millis() - openedAt > OPEN_LIMIT_MS) {
    sendEvent("alarm");
    alarmActive = true;
    lastAlarmBeep = millis() - 1000;   // beep right away
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Open too long!");
    lcd.setCursor(0, 1);
    lcd.print("Close with 'D'");
  }

  // While the alarm is active, beep once per second
  if (alarmActive && millis() - lastAlarmBeep >= 1000) {
    lastAlarmBeep = millis();
    playTone(2500, 200);
  }
}

void handleKey(char key) {
  if (waitingResult) return;

  if (phase == PHASE_OPEN) {
    if (key == 'D') {
      playTone(1000, 100);
      playTone(750, 100);
      playTone(500, 100);
      sendEvent(alarmActive ? "closed_late" : "closed");
      resetForm();                // back to the PIN prompt
    }
    return;                       // ignore every other key
  }

  playTone(1000, 50);

  if (key >= '0' && key <= '9') {
    if (input.length() < MAX_LEN) {
      input += key;
      renderInput();
      showHint();
    }
  }
  else if (key == '*') {
    input = "";
    renderInput();
    showHint();
  }
  else if (key == '#') {
    if (input.length() < MIN_LEN) {
      showBottom("Need 4-6 digits");
      return;
    }

    if (phase == PHASE_PIN) {
      pin = input;
      input = "";
      phase = PHASE_PASSCODE;
      showPrompt();
    } else {
      passcode = input;
      submit();    // the reset happens in checkResult()
    }
  }
  // A, B, C, D are ignored in the login phases
}

// ---------- Arduino ----------
void setup() {
  Serial.begin(19200);

  // Servo: attach once, 50 Hz, 14-bit, and hold it still
  bool ok = ledcAttachChannel(SERVO_PIN, 50, 14, SERVO_CHANNEL);
  Serial.println(ok ? "servo PWM attached" : "servo PWM FAILED");
  ledcWrite(SERVO_PIN, servoDuty(SERVO_STOP_US));

  // --- BLE setup ---
  pinMode(23, OUTPUT);
  BLEDevice::init("Them Crooked Vultures");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pLedStateChar = pService->createCharacteristic(
    LED_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE);
  uint8_t off = 0;
  pLedStateChar->setValue(&off, 1);

  pCredChar = pService->createCharacteristic(
    CRED_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

  pResultChar = pService->createCharacteristic(
    RESULT_UUID,
    BLECharacteristic::PROPERTY_WRITE);

  pEventChar = pService->createCharacteristic(
    EVENT_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

  pResultChar->setCallbacks(new ResultCallbacks());

  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->start();
  // --- end BLE setup ---

  // LCD
  lcd.init();
  lcd.backlight();

  // Buzzer
  pinMode(BUZZER_PIN, OUTPUT);

  setupNumpad();
  showPrompt();

  Serial.println("advertising");
}

void loop() {
  if (pLedStateChar->getLength() >= 1) {
    digitalWrite(23, *pLedStateChar->getData());
  }

  char key = readNumpad();
  if (key && key != lastKey) handleKey(key);
  lastKey = key;

  checkResult();
  checkOpenTimeout();
  delay(20);
}