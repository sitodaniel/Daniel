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

## ¿Qué es un bloque de código?

Un **bloque de código** es un conjunto de instrucciones que se agrupan y se ejecutan juntas bajo una misma condición o estructura.

Por ejemplo, el contenido dentro de un `if`, un `while`, un `for`, una función (`def`) o una clase (`class`) se considera un **bloque**.

```python
if True:
    print("Esto forma parte del bloque")  # ← línea dentro del bloque
print("Esto ya no pertenece al bloque")   # ← fuera del bloque
```

## ¿Qué es la identación?
La identación es el espacio en blanco que se deja al inicio de una línea para indicar que esa línea forma parte de un bloque.

En Python, la identación no es opcional: si te equivocas en ella, el código no funciona.
Esto hace que tu código sea más ordenado y fácil de leer.

## ¿Cuántos espacios debo usar?
Por convención (PEP 8), se recomienda usar 4 espacios por nivel de indentación

```python
if True:
    print("Este código está indentado correctamente")
```

## Ejemplo de una identacion incorrecta

```python
if True:
  print("Esto tiene solo 2 espacios")
    print("Esto tiene 4")  # Python se enfada aquí
```

## Ejemplo correcto

```python
if True:
    print("Línea 1 del bloque")
    print("Línea 2 del mismo bloque")
print("Fuera del bloque")
```
