import os
import time
import asyncio

import random

from abc import ABC, abstractmethod

from itertools import cycle

# ключевые параметры
NORMAL_TIMER_LIMIT = 10     # базовое временное ограничение приоритета светофора
MAX_TRAFFIC_ADD = 10        # максимальный показатель прироста трафика за шаг
WARNING_TRAFFIC_LIMIT = 30  # предел нормальной загруженности светофора 

# симуляция увеличения трафика в течении дня
TRAFFIC_LEVEL = 1           # текущий коэфициент загруженности
DAY_TRAFFIC_LEVEL = cycle([1,1,2,2,3,3,4,4,5,5,6,7,6,5,5,4,4,3,3,2,2,1,1]) # набор дневных коэффициентов


########################################  абстрактный класс светофора #################################################
class UniversalTrafficLight(ABC):

    def __init__(self, 
                 id: int, camera, priority: bool, conn_status:bool = False, 
                 slave_auto_lights:list = [], slave_people_lights:list = []) -> None:
        self.id = id                                    # уникальный идентификатор
        self.camera = camera                            # данные камеры трафика 
        self.priority = priority                        # приоритет 
        self.priority_index = 0                         # индекс приоритета 
        self.state = "RED"                              # состояние светофора (по умолчанию)
        self.queue_size = -100                          # размер очереди перед светофором (данные из camera) 
        self.timer = None                               # таймер 
        self.event_queue = []                           # очередь сообщений 
        self.conn_status = conn_status                  # статус сети
        self.slave_auto_lights = slave_auto_lights      # список зависимых авто светофоров
        self.slave_people_lights = slave_people_lights  # список зависимых пешеходных светофоров


    # получить текущий цвет
    def get_state(self)-> str:
        return self.state


    # установить текущий цвет 
    def set_state(self, state: str)-> None:
        self.state = state


    # получить размер очереди перед светофором
    def get_queue_size(self)-> int:
        return self.queue_size


    # установить размер очереди перед светофором
    def set_queue_size(self, queue_size:int)->None:
        self.queue_size = queue_size


    # получить приоритет
    def get_priority(self)-> bool:
        return self.priority


    # установить приоритет
    def set_priority(self, priority:bool)-> None:
        self.priority = priority


    # получить индекс приоритета
    def get_priority_index(self)-> int:
        return self.priority_index
    

    # установить индекс приоритета
    def set_priority_index(self, priority_index:int)-> None:
        self.priority_index = priority_index  


    # получить статус подключения
    def get_conn_status(self)-> bool:
        return self.conn_status
    

    # установить статус подключения
    def set_conn_status(self, conn_status:bool)-> None:
        self.conn_status = conn_status      


    # добавить сообщение в очередь сообщений
    def send_event(self, event:dict)->None:
        self.event_queue.append(event)


    # обработчик очереди сообщений
    async def process_events(self, traffic_lights: list)-> None:
        # пока очередь сообщений не пуста
        while self.event_queue:
            event = self.event_queue.pop(0)                        # считывание первого сообщения 
            await self.handle_event(event, traffic_lights)         # передача сообщения в обработчик сообщений       


    # обработчик сообщений
    async def handle_event(self, event, traffic_lights: list)-> None:
        other = traffic_lights[event["sender"]-1]
        # сообщение запроса приоритета
        if event["type"] == "PRIORITY_REQUEST":
            # проверка статуса сети принимающего устройства
            if other.conn_status:
                if other.queue_size > self.queue_size:
                    # отправка подтверждения приоритета для другого светофора   
                    other.send_event({
                        "type": "PRIORITY_GRANTED",
                        "sender": self.id
                        })    
        # сообщение подтверждения приоритета                 
        elif event["type"] == "PRIORITY_GRANTED":
            self.priority_index += 1
            # количества on-line светофоров
            online_traffic_lights = list(filter(lambda x: x.conn_status == True, 
                                                [traffic_light for traffic_light in traffic_lights]))
            # проверяем порог установки приоритета (зависит от количества on-line светофоров)  
            if self.priority_index == len(online_traffic_lights) - 1:
                status = 'получил приоритет'
                await self.grant_priority(status)         # включение приоритета


    # запрос приоритета у остальных светофоров
    async def request_priority(self, other)-> None:
        # проверка статуса сети принимающего устройства
        if other.conn_status: 
            # отправка запроса приоритета только on-line устройствам
            other.send_event({
                "type": "PRIORITY_REQUEST",
                "sender": self.id,
                "trafic": self.queue_size
            })


    # контейнер статуса подключения к сети
    """
    отправляет пакет CONN_STATUS, который определяет доступность светофора в сети
    """    
    def connection_status(self)-> None:
        # отправка запроса приоритета
        for other in traffic_lights:
            if other.id != self.id:
                other.send_event({
                    "type": "CONN_STATUS",
                    "sender": self.id,
                    "status": self.conn_status
                })    


    # установка приоритета (абстрактный метод)   
    @abstractmethod
    async def grant_priority(self)-> None:
        pass


    # установка приоритета зависимым светофорам
    async def other_grant_priority(self)-> None:
        # установка приоритета авто светофорам
        for slave_auto in self.slave_auto_lights:
            other_auto = auto_lights[slave_auto-1]
            if not other_auto.priority and other_auto.queue_size != 0 and other_auto.conn_status:
                await other_auto.grant_priority('подключил зависимый авто светофор')

        # установка приоритета пешеходным светофорам
        for slave_people in self.slave_people_lights:
            other_people = people_lights[slave_people-5]
            if not other_people.priority  and other_people.queue_size != 0 and other_people.conn_status:
                await other_people.grant_priority('подключил зависимый пешеходный светофор')


    # сброс приоритета
    async def drop_priority(self)-> None:
        if self.get_priority():
            # сброс приоритета по встроенному временному таймеру
            traffic_coef = self.queue_size // 10 # множитель трафика (тем больше, чем выше трафик перед светофором)
            self.timer = asyncio.get_event_loop().call_later(NORMAL_TIMER_LIMIT*traffic_coef, self.timer_expired) # таймер сброса по времени (от 10с)
            
            # сброс приоритета по трафику (0шт)
            if self.get_priority():
                while self.get_queue_size() > 0 and self.get_priority():
                    await asyncio.sleep(0.33)
                    queue_size = self.get_queue_size()
                    queue_size -= 1
                    self.set_queue_size(queue_size)
                    crossroads_status()
                    self.timer.cancel()                     # сброс таймера времени
                self.set_priority(False)                    # сброс приоритета    
                status = 'утратил приоритет по трафику'
                await self.green_to_red(status)
        else:       
            status = 'приоритет сброшен другим светофором'
            await self.green_to_red(status)             


    # сброс приоритета другим 
    async def other_drop_priority(self)-> None:
        # сброс приоритета зависимым авто светофорам
        for slave in self.slave_auto_lights:
            auto_slave = auto_lights[slave-1]
            if auto_slave.get_priority():
                auto_slave.set_priority(False)
                self.drop_priority(auto_slave)    

        # сброс приоритета зависимым пешеходным светофорам
        for slave in self.slave_people_lights:
            people_slave = people_lights[slave-5]
            if people_slave.get_priority():
                people_slave.set_priority(False)
                self.drop_priority(people_slave)           


    # прерывание приоритета по времени (связка с таймером сброса по времени)
    async def timer_expired(self)-> None:
        self.set_priority(False)                            # сброс приоритета
        status = 'утратил приоритет по времени'             # причина сброса приоритета
        await self.green_to_red(status)                     # переключение светофора на красный         


    # смена сфетофора с зеленого на красный (абстрактный метод)   
    @abstractmethod
    async def green_to_red(self, status = '...')-> None:
        pass


    # смена сфетофора с красного на зеленый (абстрактный метод)   
    @abstractmethod
    async def red_to_green(self, status = '...')-> None:
        pass


    # функция управления светофором
    @property
    async def traffic_light_control(self)->None:
        # аварийный режим при потере связи
        if not self.conn_status:
            self.set_state('YELLOW')    

        # отправка статуса состояния сети другим светофорам (30сек)   
        self.status_timer = asyncio.get_event_loop().call_later(30, self.connection_status)    

        # начальный трафик с камеры контроля
        if self.get_queue_size() < 0:
            self.set_queue_size(self.camera.get_queue_size())
        # обновление данных трафика с камеры контроля    
        else:
            self.set_queue_size(self.get_queue_size() + random.randrange(0,MAX_TRAFFIC_ADD*TRAFFIC_LEVEL))  

        # установка приоритета по трафику другому светофору   
        for other in traffic_lights:
            # только для других светофоров
            if other.id != self.id:
                # проверка других светофоров перед отправкой приоритета по трафику
                """
                на длину очереди, 
                очередь больше чем у текущего светофора, 
                отсутствие приоритета, 
                устройство on-line
                """
                if (other.queue_size > WARNING_TRAFFIC_LIMIT and 
                    self.queue_size < other.queue_size and 
                    not other.priority and
                    other.conn_status):
                    await other.grant_priority('получил приоритет по максимальному трафику')
                await self.request_priority(other)               # запрос приоритета у другого светофора
        await self.process_events(traffic_lights)                # запуск обработчика очереди сообщений 
#####################################  конец класса абстрактного светофора ###########################################



########################################### класс автомобильного светофора ###########################################
class AutoTrafficLight(UniversalTrafficLight):

    def __init__(self, id:int, camera, priority:bool, conn_status:bool = False, 
                 slave_auto_lights:list = [], slave_people_lights:list = [])-> None:
        super().__init__(id, camera, priority, conn_status, 
                         slave_auto_lights, slave_people_lights) # переменные родительского класса (можно не использовать)

    # метод установки приоритета (переопределяем)   
    async def grant_priority(self, status:str)-> None:
        # сброс возможных конфликтных приоритетов
        for other_auto in auto_lights:
            # выборка не зависимых светофоров
            if other_auto.id not in self.slave_auto_lights:
                if other_auto.get_priority():
                    # если трафик перед светофором больше других не зависимых светофоров
                    if other_auto.get_queue_size() < self.get_queue_size():
                        other_auto.set_priority(False)
                        await other_auto.drop_priority()    # сброс приоритета другому светофору  
                    else:
                        status = 'заблокировал получение приоритета по трафику'
                        crossroads_status(f'Светофор {other_auto.id}', status) # обновление панели    
                else:
                    if self.queue_size != 0 and self.conn_status:
                        self.set_priority(True)             # установка приоритета            
                        await self.red_to_green(status)     # переключение светофора на зеленый
                        await self.drop_priority()          # запуск таймеров сброса

                        # установка приоритета зависимым светофорам
                        await self.other_grant_priority()

                    
    #  смена светофора с зеленого на красный 
    async def green_to_red(self, status:str = '...')-> None:
        self.set_state("YELLOW")                            # установка желтого сигнала (1 с.)
        crossroads_status()                                 # обновление панели    
        time.sleep(0.33)
        self.set_state("RED")                               # установка красного сигнала
        crossroads_status(f'Светофор {self.id}', status)    # обновление панели


    #  смена светофора с красного на зеленый 
    async def red_to_green(self, status:str = '...')-> None:
        self.set_state("YELLOW")                            # установка желтого сигнала (1 с.)
        crossroads_status()                                 # обновление панели    
        time.sleep(0.33)
        self.set_state("GREEN")                             # установка красного сигнала
        crossroads_status(f'Светофор {self.id}', status)    # обновление панели
###################################### конец класса автомобильного светофора ##########################################



######################################## класс пешеходного светофора ##################################################
class PeopleTrafficLight(UniversalTrafficLight):

    def __init__(self, id:int, camera, priority:bool, conn_status:bool = False, 
                 slave_auto_lights:list = [], slave_people_lights:list = [])-> None:
        super().__init__(id, camera, priority, conn_status, 
                         slave_auto_lights, slave_people_lights) # переменные родительского класса (можно не использовать)

    # метод установки приоритета (переопределяем)   
    async def grant_priority(self, status:str)-> None:
        # сброс возможных конфликтных приоритетов
        for other_people in people_lights:
            # выборка не зависимых светофоров
            if other_people.id not in self.slave_auto_lights:
                if other_people.get_priority():
                    # если трафик перед светофором больше других не зависимых светофоров
                    if other_people.get_queue_size() < self.get_queue_size():
                        other_people.set_priority(False)
                        await other_people.drop_priority()            # сброс приоритета другому светофору  
                    else:
                        status = 'заблокировал получение приоритета по трафику'
                        crossroads_status(f'Светофор {other_people.id}', status) # обновление панели    
                else:
                    if self.queue_size != 0 and self.conn_status: 
                        self.set_priority(True)                 # установка приоритета            
                        await self.red_to_green(status)         # переключение светофора на зеленый
                        await self.drop_priority()              # запуск таймеров сброса

                        # установка приоритета зависимым светофорам
                        await self.other_grant_priority()


    #  смена светофора с зеленого на красный 
    async def green_to_red(self, status:str = '...')-> None:
        self.set_state("RED")                               # установка красного сигнала
        crossroads_status(f'Светофор {self.id}', status)    # обновление панели


    #  смена светофора с красного на зеленый 
    async def red_to_green(self, status:str = '...')-> None:
        self.set_state("GREEN")                             # установка красного сигнала
        crossroads_status(f'Светофор {self.id}', status)    # обновление панели
#################################### конец класса пешеходного светофора ################################################



############################################### класс камеры ###########################################################
class Camera:
    def __init__(self)-> None:
        self.queue_size = random.randrange(0,MAX_TRAFFIC_ADD)

    # получить размер очереди перед светофором
    def get_queue_size(self)-> int:
        #print(f"Обновление данных от камеры светофора")
        return self.queue_size
############################################### конец класса камеры ####################################################



############################################# Блок управляющих функций #################################################
# подключение светофоров к перекрестку
def create_lights()-> tuple:
    # экземпляры автомобильных светофоров
    auto_lights = [
        AutoTrafficLight(1, Camera(), False, True, [2], [7,8,11,12]),
        AutoTrafficLight(2, Camera(), False, True, [1], [7,8,11,12]),
        AutoTrafficLight(3, Camera(), False, True, [4], [5,6,9,10]),
        AutoTrafficLight(4, Camera(), False, True, [3], [5,6,9,10])
        ]
    
    # экземпляры пешеходных светофоров
    people_lights = [
        PeopleTrafficLight(5, Camera(), False, False, [4], [6]),
        PeopleTrafficLight(6, Camera(), False, False, [4], [5]),
        PeopleTrafficLight(7, Camera(), False, False, [2], [8]),
        PeopleTrafficLight(8, Camera(), False, False, [2], [7]),
        PeopleTrafficLight(9, Camera(), False, False, [3], [10]),
        PeopleTrafficLight(10, Camera(), False, False, [3], [9]),
        PeopleTrafficLight(11, Camera(), False, False, [1], [12]),
        PeopleTrafficLight(12, Camera(), False, False, [1], [11])
        ]
    return auto_lights, people_lights


# опрос светофоров перекрестка
def crossroads_status(current_id:str = 'Обновлений', status:str = 'НЕТ')-> None:
    time.sleep(1)
    os.system(['clear', 'cls'][os.name == os.sys.platform])
    print('*'*11, 'Current crossroads status:', '*'*11) 
    print(f'{current_id} - {status}')

    # вывод информации об автомобильных светофорах
    print('*'*15, 'Auto traffic light:', '*'*15)
    for auto_light in auto_lights:
        current_queue_size = auto_light.get_queue_size()
        print(auto_light.id, auto_light.state, current_queue_size, 
              f'{"on-line" if auto_light.conn_status == True else "off-line"}') 
    
    # вывод информации о пешеходных светофорах
    print('*'*14, 'People traffic light:', '*'*14)    
    for people_light in people_lights:
        current_queue_size = people_light.get_queue_size()
        print(people_light.id, people_light.state, current_queue_size, 
              f'{"on-line" if people_light.conn_status == True else "off-line"}') 



# главная компилирующая функция перекрестка   
async def main(auto_lights, people_lights):   
    global TRAFFIC_LEVEL

    while True:
        TRAFFIC_LEVEL = next(DAY_TRAFFIC_LEVEL)
        # список коррутин обновления для светофоров перекрестка
        auto_lights_control_func = [
            auto_light.traffic_light_control
            for auto_light in auto_lights
            ]
        
        people_lights_control_func = [
            people_light.traffic_light_control
            for people_light in people_lights
            ]
        
        auto_lights_control_func.extend(people_lights_control_func)

        # конкурентный запуск светофоров
        await asyncio.gather(*auto_lights_control_func)
        crossroads_status()
############################################# конец блока управляющих функций ##########################################


# точка входа
if __name__ == '__main__':
    auto_lights, people_lights = create_lights()        # набор автомобильных и пешеходных светофоров
    traffic_lights = auto_lights.copy()
    traffic_lights.extend(people_lights)
    asyncio.run(main(auto_lights, people_lights))                   # запуск цикла событий