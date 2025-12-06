import serial
import time
import csv

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/cu.usbserial-1140'  # <--- CHANGE THIS to your port!
BAUD_RATE = 9600
OUTPUT_FILENAME = 'emg_data_ard.csv'

def main():
    # Connect to the Arduino
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}")
        print("Waiting for data... (Flex your arm!)")
        print("Press Ctrl+C to stop recording.")
    except serial.SerialException:
        print(f"ERROR: Could not open port {SERIAL_PORT}.")
        print("Make sure Arduino IDE is closed and the port name is correct.")
        return

    # Allow Arduino to reset
    time.sleep(2)

    # Open the file to save data
    with open(OUTPUT_FILENAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "EMG_Value"]) # Write Header

        try:
            while True:
                # Read a line from Arduino
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8').strip()
                        if line: # If the line is not empty
                            current_time = time.time()
                            writer.writerow([current_time, line])
                            print(f"Recorded: {line}") # Print to screen so you know it's working
                    except UnicodeDecodeError:
                        continue # Skip bad data packets
        except KeyboardInterrupt:
            print("\nRecording stopped.")
            print(f"Data saved to {OUTPUT_FILENAME}")
        finally:
            ser.close()

if __name__ == "__main__":
    main()