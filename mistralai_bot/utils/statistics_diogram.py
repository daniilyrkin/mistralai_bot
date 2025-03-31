import matplotlib.pyplot as plt
import io
from collections import defaultdict
from datetime import datetime, timedelta


class Diagram_creator:

    def __init__(self, data):

        self.data = data
        self.counts = ()
        self.days = ()

    def prepare_data_for_plot_month(self):
        # Словарь для хранения количества запросов по дням
        requests_by_month = defaultdict(int)

        for request in self.data:
            # Приводим дату к формату "день-месяц-год" для группировки
            month = request.created.strftime('%Y-%m')
            requests_by_month[month] += 1

        # Преобразуем данные в списки для построения графика
        self.days = list(requests_by_month.keys())
        self.counts = list(requests_by_month.values())

    def prepare_data_for_plot_day(self):
        requests_by_day = defaultdict(int)
        # Вычисляем дату, которая была 30 дней назад
        last_month = datetime.now() - timedelta(days=30)

        for request in self.data:
            # Фильтруем данные, оставляя только те, что созданы за последние 30 дней
            if request.created >= last_month:
                day = request.created.strftime('%Y-%m-%d')  # Группируем по дням
                requests_by_day[day] += 1

        # Сортируем дни по возрастанию
        self.days = sorted(requests_by_day.keys())
        self.counts = [requests_by_day[day] for day in self.days]

    def plot_statistics(self, time: str):
        if time == 'month':
            self.prepare_data_for_plot_month()
        elif time == 'day':
            self.prepare_data_for_plot_day()
        plt.figure(figsize=(10, 5))
        plt.plot(self.days, self.counts, marker='o', linestyle='--', color='b')
        plt.title('Количество запросов')
        plt.xlabel('Дата')
        plt.xticks(rotation=45)  # Поворот подписей дат для удобства
        plt.grid(True)
        # Добавление числовых значений к точкам
        for i, (day, count) in enumerate(zip(self.days, self.counts)):
            plt.annotate(f'{count}', (day, count), textcoords="offset points", xytext=(0, 10), ha='center')

        plt.tight_layout()

        # Сохранение графика в байтовый поток
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf
