## Упражнение c декораторами

### Краткое описание
Реализовано несколько простых функций и декораторы к ним:
* @decorator - декорирует декоратор и присваивает ему название, описание и набор свойств от декорируемой им функции.
* @disable - декоратор-пустышка для присваивания к переменным функций-декораторов, которые необходимо отключить.
* @countcalls - считает количество вызовов декорируемой функции.
* @memo - кэширует результаты вызово декорируемой функции.
* @n_ary - позволяет вызывать декорируемую функцию с любым количеством аргументов.
* @trace - отрисовывает стек вызово декорируемой функции.

### Требования
* Установленный Python 3.4+

### Запуск
```
cd src/
python3 deco.py 
```