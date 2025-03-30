# Ejercicio 2 
---
## numero_positivo_negativo.py
haz un programa que pida un numero y diga si es positivo negativo o cero

```python

number_user = float(input("Ingresa un numero: "))

print("\nEl numero es positico, negativo o cero?\n")
if number_user == 0:
    print(f"El numero {number_user}: es cero")
elif number_user > 0:
    print(f"El numero {number_user}: es positivo")
else:
    print(f"El numero {number_user}: es negativo")
