import os
import time

import random

from abc import ABC, abstractmethod


PRIORITY_QUEUE = []

WARNING_TRAFFIC_LEVEL = 50


########################################  абстрактный класс светофора #################################################
class UniversalTrafficLight(ABC):

    def __init__(self, id, camera, priority):
        self.id = id                   # уникальный идентификатор
        self.camera = camera           # данные камеры трафика 
        self.priority = priority       # приоритет 
        self.state = {"RED": True, "GREEN": False}             # состояние светофора (по умолчанию)
        self.queue_size = -100            # размер очереди перед светофором (данные из camera) 
        self.timer = None              # таймер 
        self.event_queue = []          # очередь сообщений 
 

    # получить текущий цвет
    def get_state(self):
        for key, value in self.state.items():
            if value:
                return key
        status = 'ошибка индикации'    
        crossroads_status(f'Светофор {self.id}', status)
        return "YELLOW"    


    # установить текущий цвет 
    def set_state(self, state):
        current_collor = self.get_state()
        self.state[current_collor] = False
        self.state[state] = True


    # получить размер очереди перед светофором
    def get_queue_size(self):
        return self.queue_size


    # установить размер очереди перед светофором
    def set_queue_size(self, queue_size):
        self.queue_size = queue_size


    # получить приоритет
    def get_priority(self):
        return self.priority


    # установить приоритет
    def set_priority(self, priority):
        self.priority = priority


    # добавить сообщение в очередь сообщений
    def send_event(self, event):
        self.event_queue.append(event)


    # обработчик очереди сообщений
    def process_events(self):
        status = f'обработал сообщения'
        crossroads_status(f'Светофор {self.id}', status)
        # пока очередь сообщений не пуста
        while self.event_queue:
            event = self.event_queue.pop(0)    
            self.handle_event(event)         # передача сообщения в обработчик сообщений       


    # обработчик сообщений     
    def handle_event(self, event):
        # указываем светофор назначения
        other = traffic_lights[event["sender"]-1]
        # проверяем тип сообщения
        if event["type"] == "PRIORITY_REQUEST":
            # проверяем основание для приоритета по трафику и отсутствие действующего приоритета
            if self.queue_size < other.queue_size and not other.get_priority():
                # отправка подтверждения приоритета для другого светофора   
                other.send_event({
                    "type": "PRIORITY_GRANTED",
                    "sender": self.id
                    })    
        # сообщение подтверждения приоритета                 
        elif event["type"] == "PRIORITY_GRANTED":
            PRIORITY_QUEUE.append(self.id)


    # запрос приоритета у остальных светофоров    
    def request_priority(self, other):
        # отправка запроса приоритета
        other.send_event({
            "type": "PRIORITY_REQUEST",
            "sender": self.id,
            "trafic": self.queue_size
        })
        status = f'отправил запрос приоритета светофору {other.id}'
        crossroads_status(f'Светофор {self.id}', status)


    # установка приоритета основному   
    def grant_priority(self, status = None):
        slave_lights = [avto_lights[slave_id-1] for slave_id in adaptation_avto.get_slave_lights(self)]  
        self.set_priority(True)
        crossroads_status(f'Светофор {self.id}', status)
        self.red_to_green()
        if self.get_queue_size() > 0:
            self.set_queue_size(self.get_queue_size() - 1)
        status = f'проезд автомобиля по {self.get_state()} сигналу'
        crossroads_status(f'Светофор {self.id}', status)
        if len(PRIORITY_QUEUE) > 0:
            PRIORITY_QUEUE.pop(0)
        # установка приоритета всем зависимым авто    
        for slave_light in slave_lights:
            if not slave_light.get_priority():
                slave_light.grant_priority_for_slave_avto("получил приоритет как зависимый")
        # сброс приоритета у независимых авто
        for light in avto_lights:
            if light.id != self.id and light.id not in slave_lights:
                if light.get_priority():
                    if light.get_queue_size() <= WARNING_TRAFFIC_LEVEL:
                        light.drop_priority("потерял приоритет из-за конфликта")
                    else:
                        # восстановление приоритета всем зависимым авто    
                        for slave_light in slave_lights:
                            if not slave_light.get_priority():
                                slave_light.grant_priority_for_slave_avto("приоритет восстановлен как у зависимого")


    # установка приоритета зависимому   
    def grant_priority_for_slave_avto(self, status = None):
        self.set_priority(True)
        crossroads_status(f'Светофор {self.id}', status)
        self.red_to_green()
        if self.get_queue_size() > 0:
            self.set_queue_size(self.get_queue_size() - 1)
        status = f'проезд автомобиля по {self.get_state()} сигналу'
        crossroads_status(f'Светофор {self.id}', status)


    # сброс приоритета основному
    def drop_priority(self, status = None):
        if self.get_queue_size() <= WARNING_TRAFFIC_LEVEL:
            slave_lights = [avto_lights[slave_id-1] for slave_id in adaptation_avto.get_slave_lights(self)]
            self.set_priority(False)       
            status = 'потерял приоритет'
            crossroads_status(f'Светофор {self.id}', status)
            self.green_to_red()  
            # сброс приоритета всем зависимым авто    
            for slave_light in slave_lights:
                if slave_light.get_priority():
                    slave_light.drop_priority_for_slave()


    # сброс приоритета зависимому
    def drop_priority_for_slave(self):
        slave_lights = [avto_lights[slave_id-1] for slave_id in adaptation_avto.get_slave_lights(self)]
        if self.get_priority():
            if self.get_queue_size() <= WARNING_TRAFFIC_LEVEL:
                self.set_priority(False)       
                status = 'потерял приоритет как зависимый'
                crossroads_status(f'Светофор {self.id}', status)
                self.green_to_red()
            else:
                # восстановление приоритета всем зависимым авто    
                for slave_light in slave_lights:
                    if not slave_light.get_priority():
                        slave_light.grant_priority_for_slave_avto("приоритет восстановлен как у зависимого")
          

    # смена сфетофора с зеленого на красный (абстрактный метод)   
    @abstractmethod
    def green_to_red(self):
        pass


    # смена сфетофора с красного на зеленый (абстрактный метод)   
    @abstractmethod
    def red_to_green(self):
        pass


    # функция управления светофором
    @property
    def controller(self):

        adaptation_avto.check_warning_level(self) # проверка превышения опасного уровня траффика
        max_queue_size = max([light.queue_size for light in avto_lights]) # максимальный уровень трафика из всех авто

        # если приоритет еще есть
        if self.get_priority():    
            # не сбрасываем имеющийся приоритет если:   
            """ 
            - приоритет в очереди 
            - превышение опасного уровня трафика 
            """
            if ((len(PRIORITY_QUEUE)>0 and PRIORITY_QUEUE[0] == self.id) or 
                (self.queue_size > WARNING_TRAFFIC_LEVEL and self.queue_size == max_queue_size)):
                if self.get_queue_size() > 0:
                    self.set_queue_size(self.get_queue_size() - 1)
                status = f'проезд автомобиля по {self.get_state()} сигналу'
                crossroads_status(f'Светофор {self.id}', status)
                # если очередь приоритета не пуста
                if len(PRIORITY_QUEUE) > 0:
                    PRIORITY_QUEUE.pop(0) # читаем следующий приоритет 
            # снимаем приоритет
            else:    
                self.drop_priority() 

        # начальный трафик с камеры контроля
        if self.get_queue_size() < 0:
            self.set_queue_size(self.camera.get_queue_size())
            status = f'получил начальный трафик от камеры'
            crossroads_status(f'Светофор {self.id}', status)
        # обновление данных трафика с камеры контроля    
        else:
            self.set_queue_size(self.get_queue_size() + random.randrange(0,5)) 
            status = f'получил прибавку трафика от камеры'
            crossroads_status(f'Светофор {self.id}', status)

        # проверка приоритета
        if len(PRIORITY_QUEUE)>0:
            if self.id == PRIORITY_QUEUE[0] and not self.get_priority():
                status = f'получил приоритет'
                self.grant_priority(status)   
                
        # отправка запроса приоритета другим светофорам (пока приоритет не получен)
        if not self.get_priority():
            for traffic_light in avto_lights:
                if self.id != traffic_light.id:
                    self.request_priority(traffic_light) 

        # отправляем сообщения из очереди в обработчик            
        self.process_events()       
#####################################  конец класса абстрактного светофора ###########################################



########################################### класс автомобильного светофора ###########################################
class AvtoTrafficLight(UniversalTrafficLight):

    # переключение на зеленый (через желтый)
    def red_to_green(self):
        if self.get_state() == "RED":
            self.set_state("YELLOW")
            status = f'переключился на желтый'
            crossroads_status(f'Светофор {self.id}', status)    
            time.sleep(1)
            self.set_state("GREEN")
            status = f'переключился на зеленый'
            crossroads_status(f'Светофор {self.id}', status)
  

    # переключение на красный (через желтый)
    def green_to_red(self):
        if self.get_state() == "GREEN":
            self.set_state("YELLOW")
            status = f'переключился на желтый'
            crossroads_status(f'Светофор {self.id}', status)
            time.sleep(1)
            self.set_state("RED")
            status = f'переключился на красный'
            crossroads_status(f'Светофор {self.id}', status)
###################################### конец класса автомобильного светофора ##########################################



######################################## класс пешеходного светофора ##################################################
class PeopleTrafficLight(UniversalTrafficLight):

    # переключение на зеленый
    def red_to_green(self):
        if self.get_state() == "RED":
            self.set_state("GREEN")
            status = f'переключился на зеленый'
            crossroads_status(f'Светофор {self.id}', status)

    # переключение на красный
    def green_to_red(self):
        if self.get_state() == "GREEN":
            self.set_state("RED")
            status = f'переключился на красный'
            crossroads_status(f'Светофор {self.id}', status)
#################################### конец класса пешеходного светофора ################################################



############################################### класс камеры ###########################################################
class Camera:
    def __init__(self):
        self.queue_size = random.randrange(0,2)

    # получить размер очереди перед светофором
    def get_queue_size(self):
        #print(f"Обновление данных от камеры светофора")
        return self.queue_size
############################################### конец класса камеры ####################################################



############################################### класс адаптивного модуля ################################################
class Adaptation:
    def __init__(self, lights):
        self.lights = lights
        self.slave_lights = {}

    def get_slave_lights(self, current_light):
        return self.slave_lights.get(current_light.id)    

    def set_slave_lights(self, slave_lights):
        self.set_slave_lights = slave_lights      

    # формируем список зависимых светофоров
    def create_slave(self, current_light):
        if current_light.id%2 == 0:
            self.slave_lights.setdefault(current_light.id, 
                                         [light.id for light in self.lights 
                                          if light.id%2 == 0 and light.id != current_light.id])
        else:
            self.slave_lights.setdefault(current_light.id, 
                                         [light.id for light in self.lights 
                                          if light.id%2 != 0 and light.id != current_light.id])

    def check_warning_level(self, other):
        if other.queue_size > WARNING_TRAFFIC_LEVEL and other.queue_size == max([light.queue_size for light in avto_lights]):
            if not other.get_priority():
                other.grant_priority('получил приоритет по максимальному трафику') 
############################################### конец адаптивного модуля ###############################################



############################################# Блок управляющих функций #################################################


# подключение светофоров к перекрестку
def create_lights():

    # экземпляры автомобильных светофоров
    avto_lights = [
        AvtoTrafficLight(1, Camera(), False),
        AvtoTrafficLight(2, Camera(), False),
        AvtoTrafficLight(3, Camera(), False),
        AvtoTrafficLight(4, Camera(), False)
        ]
    
    # экземпляры пешеходных светофоров
    people_lights = [
        PeopleTrafficLight(5, Camera(), False),
        PeopleTrafficLight(6, Camera(), False),
        PeopleTrafficLight(7, Camera(), False),
        PeopleTrafficLight(8, Camera(), False),
        PeopleTrafficLight(9, Camera(), False),
        PeopleTrafficLight(10, Camera(), False),
        PeopleTrafficLight(11, Camera(), False),
        PeopleTrafficLight(12, Camera(), False)
        ]
    return avto_lights, people_lights


# подключение адаптаций светофоров
def connect_adaptation():

    # экземпляры адаптационного модуля
    adaptation_avto = Adaptation(avto_lights)           # подключение модуля адаптации для авто
    adaptation_people = Adaptation(people_lights)       # подключение модуля адаптации для пешеходов
    
    return adaptation_avto, adaptation_people


# опрос светофоров перекрестка
def crossroads_status(current_id = 'Обновлений', status = 'НЕТ'):
    time.sleep(1)
    os.system(['clear', 'cls'][os.name == os.sys.platform])
    print('*'*11, 'Current crossroads status:', '*'*11) 
    print(f'{current_id} - {status}')

    # вывод информации об автомобильных светофорах
    print('*'*15, 'Auto traffic light:', '*'*15)
    for avto_light in avto_lights:
        current_queue_size = avto_light.get_queue_size()
        print(avto_light.id, avto_light.get_state(), avto_light.get_priority(), current_queue_size) 
    
    # вывод информации о пешеходных светофорах
    #print('*'*14, 'People traffic light:', '*'*14)    
    #for people_light in people_lights:
    #    current_queue_size = people_light.get_queue_size()
    #    print(people_light.id, people_light.state, current_queue_size) 


# главная компилирующая функция перекрестка   
def main():     
    while True:
        for avtolight in avto_lights:
            # если список зависимостей светофора пуст
            if not adaptation_avto.slave_lights.get(avtolight.id):
                adaptation_avto.create_slave(avtolight)         # подготовка зависимостей авто светофоров
            avtolight.controller  
############################################# конец блока управляющих функций ##########################################


# точка входа
if __name__ == '__main__':
    avto_lights, people_lights = create_lights()                # набор автомобильных и пешеходных светофоров

    adaptation_avto, adaptation_people = connect_adaptation()   # экземпляры класса адаптации    

    traffic_lights = avto_lights.copy()                     
    traffic_lights.extend(people_lights)                        # сообщество всех светофоров перекрестка

    main()                                                      # запуск цикла событий
    