# To write a short comment, use the # symbol. Everything after # will be ignored by Python.
# For longer explanations, you can use triple quotes (''' or """). This is often used for documentation or large notes.
    ```python
    '''
    This is a multi-line comment.
    You can write several lines of text here.
    Python will ignore all of this.
    '''

# Write a program that prints the message 'Hello, World' on the screen
    '''python
    print("Hello, World")

""" 
The print() function in Python tells the computer to display something on the screen. 
It can show text, numbers, variables, or even the result of operations.
print() is like telling the computer: “Hey! Show this on the screen!” 
""" 

# Programs use variables to store information

# 1. Create a variable in Python
    '''python
    name = "Daniel"

# 2. Use snake_case to name a variable with multiple words
    '''python
    name_user = "DanielUser"

# Variables can store different types of values like integer, float, string, and boolean.
# 3. Create variables of each basic type and print a message combining them

    '''python
    variable_one = 30               # Integer
    variable_two = 17.5             # Float
    variable_three = "Daniel"       # String The string value must be enclosed in quotation marks ("")
    variable_four = True            # Boolean

# Print a combined message using an f-string
print(f"These are the basic value types: {variable_one}, {variable_two}, {variable_three}, {variable_four}")

""" 
What is an f-string in Python? 
An f-string (short for formatted string) is a special 
type of string in Python that lets you insert variables 
directly into a string using curly braces {}. 
"""

    '''python
    name = "Daniel"
    print(f"Hello, {name}!")  # Output: Hello, Daniel!

# Do operations like addition, subtraction, multiplication, and division. Also, concatenate two strings to form a greeting.

    '''python
    # Define two numbers
    number_one = 10
    number_two = 5
    
    # Perform basic math operations
    addition = number_one + number_two          # 15
    subtraction = number_one - number_two       # 5
    multiplication = number_one * number_two    # 50
    division = number_one / number_two           # 2.0
    
    print(f"addition: {addition}")
    print(f"subtraction: {subtraction}")
    print(f"multiplication: {multiplication}")
    print(f"division: {division}")
    
    # String Concatenation (joining two strings)
    # Define a name and a greeting
    first_name = "Daniel"
    greeting = "Hello, "
    
    # Combine both strings using +
    full_greeting = greeting + first_name
    
    # Print the full greeting
    print(full_greeting)  # Output: Hello, Daniel
