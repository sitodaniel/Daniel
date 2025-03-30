# 💻 Daniel's Code Notebook

Welcome to my personal practice repo!

Here I document the Python exercises I'm working on as I learn to code.  
Everything you see here is created from scratch, without AI assistance or external help — just me learning, making mistakes, and improving every day.  
If you see something wrong, feel free to help me out (thank you in advance 😄).

---

## 🐍 Python Example

## If / elif / else
**exercise 1**

### mayor_de_dos.py
Write a program that asks for two numbers and prints which one is greater.

```python
numero_uno = int(input("Enter the first number: "))
numero_dos = int(input("Enter the second number: "))

if numero_uno > numero_dos:
    print(f"The greater number is: {numero_uno}")
elif numero_dos > numero_uno:
    print(f"The greater number is: {numero_dos}")
else:
    print("Both numbers are equal")
```
##  Explanation of the exercise 
input() is a Python function that asks the user to type something using the keyboard.

How it works step by step:
input() always stores what the user types as a string (str).
Inside the parentheses you can add a message in quotes to prompt the user.

```python
name = input("What's your name?: ")  # Text prompt goes inside quotes
```
Even if you type 123, it’s still stored as a string like "123".
To work with numbers, you must convert it:

```python
number = int(input("Enter a number: "))   # For integers
number = float(input("Enter a number: ")) # For decimal numbers
```
### if / elif / else
if means "if this condition is true, do this..."
elif is short for “else if”, and it runs if the first condition was false and this one is true.
else is the final fallback — it runs only if none of the previous conditions were met.

```python
age = 10

if age >= 18:
    print("You're an adult")
elif age >= 13:
    print("You're a teenager")
else:
    print("You're a child")
```

### Comparison Operators in Python

Comparison operators are used to compare values and return a Boolean result: `True` or `False`. 
They are essential when using `if`, `elif` y `else`.

| Operator | Meaning                | Example   | Result    |
|----------|------------------------|-----------|-----------|
| `==`     | Equal to               | `5 == 5`  | `True`    |
| `!=`     | Not equal to           | `5 != 3`  | `True`    |
| `>`      | Greater than           | `7 > 3`   | `True`    |
| `<`      | Less than              | `2 < 1`   | `False`   |
| `>=`     | Greater or equal to    | `5 >= 5`  | `True`    |
| `<=`     | Less or equal to       | `4 <= 3`  | `False`   |

## What is a block of code?

A **code block** is a group of instructions that are executed together under a specific structure.

For example, everything inside an `if`, `while`, `for`, `def`, or `class` is a block.

```python
if True:
    print("This line is part of the block")
print("This line is outside the block")
```

## What is indentation?
**Indentation** is the white space at the beginning of a line that tells Python the line is part of a block.

In Python, indentation is not optional — if it’s wrong, your code won’t run.
This rule makes Python code more readable and clean.

## How many spaces should I use?
According to the PEP 8 style guide, use 4 spaces per level of indentation.

```python
if True:
    print("This code is indented correctly")
```
⚠️ **Never mix tabs and spaces** — Python will get confused and throw an error even if it "looks" aligned to you.
## Example of incorrect indentation:

```python
if True:
  print("This line has only 2 spaces")
    print("This one has 4")  # Python will complain here
```

## Correct indentation example:

```python
if True:
    print("Line 1 of the block")
    print("Line 2 of the same block")
print("This is outside the block")
```
### 🔸 Don't forget the colon `:` after the condition

In Python, every `if`, `elif`, or `else` line **must end with a colon (`:`)**.  
This tells Python: “Hey, a code block is coming!”

Without the colon, Python will throw a syntax error.

✅ Correct:
```python
if age >= 18:
    print("You're an adult")

