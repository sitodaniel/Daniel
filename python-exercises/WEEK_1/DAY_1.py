# Write a program that prints the message 'Hello, World' on the screen

print("Hello, World")

""" The print() function in Python tells the computer to display something on the screen. 
    It can show text, numbers, variables, or even the result of operations. """
""" print() is like telling the computer: “Hey! Show this on the screen!” """ 

# Programs use variables to store information

# 1. Create a variable in Python
name = "Daniel"

# 2. Use snake_case to name a variable with multiple words
name_user = "DanielUser"

# Variables can store different types of values like integer, float, string, and boolean.
# 3. Create variables of each basic type and print a message combining them

variable_one = 30               # Integer
variable_two = 17.5             # Float
variable_three = "Daniel"       # String The string value must be enclosed in quotation marks ("")
variable_four = True            # Boolean

# Print a combined message using an f-string
print(f"These are the basic value types: {variable_one}, {variable_two}, {variable_three}, {variable_four}")

""" What is an f-string in Python? """
""" An f-string (short for formatted string) is a special 
    type of string in Python that lets you insert variables 
    directly into a string using curly braces {}. """

name = "Daniel"
print(f"Hello, {name}!")  # Output: Hello, Daniel!

