# catalog/models.py
from django.db import models

class Товары(models.Model):
    номер_товара = models.AutoField(primary_key=True)
    наименование = models.CharField(max_length=255)
    единица_измерения = models.CharField(max_length=255)
    цена = models.IntegerField()

    def __str__(self):
        return self.наименование

class Чеки(models.Model):
    номер_чека = models.AutoField(primary_key=True)
    товар = models.ForeignKey(Товары, on_delete=models.CASCADE)
    количество = models.IntegerField()
    стоимость = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.стоимость = self.товар.цена * self.количество
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.номер_чека)

class Продавцы(models.Model):
    номер_чека = models.ForeignKey(Чеки, on_delete=models.CASCADE)
    дата_покупки = models.DateField()
    номер_кассы = models.IntegerField()
    продавец = models.CharField(max_length=255)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return str(self.id)