Write a program that asks the user for a number and tells them if it is even or odd.

```python
print("\nProgram to check if a number is even or odd")  # Display title message

user_number = int(input("Enter a number: "))  # Ask the user for a number and convert it to integer

if user_number % 2 == 0:  # Check if the remainder of dividing by 2 is zero
    print("The number is even")  # If remainder is 0, it's even
else:
    print("The number is odd")  # Otherwise, it's odd
```
## What is the % (modulo) operator?
The % operator tells you what remains after dividing one number by another.

```python
10 % 2  # Result: 0  → 10 is divisible by 2 (even)
7 % 2   # Result: 1  → 7 is not divisible by 2 (odd)
```
To check if a number is even:
```python
if number % 2 == 0:
```
If it’s not (i.e., the remainder is 1), then it’s odd.
