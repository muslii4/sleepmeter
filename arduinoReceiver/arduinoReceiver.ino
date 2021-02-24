int rVal, gVal, bVal;

const int rPin = 11;
const int gPin = 10;
const int bPin = 9;

void setup() {
  Serial.begin(9600);
  pinMode(rPin, OUTPUT);
  pinMode(gPin, OUTPUT);
  pinMode(bPin, OUTPUT);
}
void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); // "255255255"
    rVal = data.substring(0, 3).toInt();
    gVal = data.substring(3, 6).toInt();
    bVal = data.substring(6, 9).toInt();

    analogWrite(rPin, rVal);
    analogWrite(gPin, gVal);
    analogWrite(bPin, bVal);
    Serial.print("Ustawiono kolor: ");
    Serial.println(String(rVal) + "." + String(gVal) + "." + String(bVal));
  }
}
