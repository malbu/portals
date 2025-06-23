const int buttonPin2 = 2;
const int buttonPin3 = 3;  // Fixed: was set to 2
int buttonState2 = 0;
int lastButtonState2 = 0;
int buttonState3 = 0;      // Added: missing variables for pin 3
int lastButtonState3 = 0;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin2, INPUT_PULLUP);
  pinMode(buttonPin3, INPUT_PULLUP);  // Added: setup for pin 3
  Serial.print("Button monitor started for Pin ");
  Serial.print(buttonPin2);
  Serial.print(" and Pin ");
  Serial.println(buttonPin3);
}

void loop() {
  // Read both button states
  buttonState2 = digitalRead(buttonPin2);  // Fixed: was buttonPin
  buttonState3 = digitalRead(buttonPin3);  // Added: read pin 3
  
  // Check pin 2
  if (buttonState2 != lastButtonState2) {  // Fixed: variable names
    if (buttonState2 == HIGH) {  // Fixed: was buttonState
      Serial.println("BUTTON2_RELEASED");  // Distinguish between buttons
    }
    delay(50); // debounce
  }
  
  // Check pin 3
  if (buttonState3 != lastButtonState3) {  // Added: check for pin 3
    if (buttonState3 == HIGH) {
      Serial.println("BUTTON3_RELEASED");
    }
    delay(50); // debounce
  }
  
  // Save current states
  lastButtonState2 = buttonState2;  // Fixed: was lastButtonState
  lastButtonState3 = buttonState3;  // Added: save pin 3 state
}