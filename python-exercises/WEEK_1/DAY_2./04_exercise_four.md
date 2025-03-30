Write a program that asks the user for a number and tells them if it is even or odd.

```python
print("\nprograma para saber si es par o impar")

numero_usuario = int(input("Ingresa el numero: "))

if numero_usuario % 2 == 0:
    print("Es numero par")
else numero_usuario % 2 == 1:
    print("Es numero impar")
