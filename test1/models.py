from django.db import models

# Create your models here.

class Exchanges(models.Model):
    name = models.CharField('名称', max_length=255, unique=True)

    def __str__(self):
        return 'Exchange:{}'.format(self.name)

class Queues(models.Model):
    name = models.CharField('名称', max_length=255, unique=True)

    def __str__(self):
        return 'Queue:{}'.format(self.name)

class Routing_keys(models.Model):
    name = models.CharField('名称', max_length=255, unique=True)
    exchange = models.ForeignKey(Exchanges, on_delete=models.CASCADE, null=True)
    queue = models.ForeignKey(Queues, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return 'Routing_key:{}'.format(self.name)


class superuser(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    create_date = models.DateTimeField('date published')

    def __str__(self):
        return 'username:{}'.format(self.username)




class Add(models.Model):
    task_id = models.CharField('任务ID', max_length=128)
    first = models.IntegerField('第一个值')
    second = models.IntegerField('第二个值')
    log_date = models.DateTimeField('创建时间')

    def __str__(self):
        return '{0}--{1}--{2}'.format(self.task_id, self.first, self.second)

    class Meta:
        verbose_name = '相加'
        verbose_name_plural = '相加'



