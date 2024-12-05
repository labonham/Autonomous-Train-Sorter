import tkinter as tk

# Function to handle state changes
def update_state():
    current_state = label_var.get()
    label.config(text=f"Current State: {current_state}")

# Function to change text color to red
def set_red():
    label.config(fg="red")

# Function to change text color to blue
def set_blue():
    label.config(fg="blue")

# Create the main window
root = tk.Tk()
root.title("Direction Switch")

# Create a StringVar to hold the current state
label_var = tk.StringVar(value="Off")  # Start with "Off"

# Create a label to display the current state
label = tk.Label(root, text=f"Current State: {label_var.get()}", font=("Helvetica", 24))
label.pack(pady=20)

# Create RadioButtons for dynamic state selection
forwards_radio = tk.Radiobutton(root, text="Forwards", variable=label_var, value="Forwards", command=update_state, font=("Helvetica", 16))
forwards_radio.pack(anchor=tk.W)

off_radio = tk.Radiobutton(root, text="Off", variable=label_var, value="Off", command=update_state, font=("Helvetica", 16))
off_radio.pack(anchor=tk.W)

backwards_radio = tk.Radiobutton(root, text="Backwards", variable=label_var, value="Backwards", command=update_state, font=("Helvetica", 16))
backwards_radio.pack(anchor=tk.W)

# Create buttons for changing the label color
red_button = tk.Button(root, text="Red", command=set_red, font=("Helvetica", 16))
red_button.pack(pady=10)

blue_button = tk.Button(root, text="Blue", command=set_blue, font=("Helvetica", 16))
blue_button.pack(pady=10)

# Start the Tkinter event loop
root.mainloop()
