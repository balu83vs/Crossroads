# Crossroads
Адаптивный алгоритм работы светофоров

<h3><b>Задача:</b></h3>
придумать и описать адаптивный алгоритм работы светофоров для
оптимизации общей пропускной способности перекрестка в зависимости от ситуации
на перекрестке.

<h3><b>Условие:</b></h3>
На перекрестке находится четыре (4 шт) светофора, регулирующих движение автомобилей 
и восемь (8 шт) светофоров, регулирующих движение пешеходов.
У пешеходных светофоров 2 состояния, у автомобильных - 3 В каждый светофор встроена
камера, которая фиксирует количество автомобилей/пешеходов в той очереди, для которых
светофор установлен. Это очередь на противоположной стороне пешехода/перекрестка (см
рисунок). Автомобили при проезде перекрестка едут либо прямо, либо направо. Люди и
автомобили осуществляют переход или проезд перекрестка по одному, уменьшая размер
соответствующей очереди на 1
Каждый светофор имеет уникальный id. Светофоры могут общаться при помощи событий, отсылая
события друг другу по id. Пересылаемые события - это некоторые контейнеры с данными
(например, там может лежать количество людей/автомобилей в очереди, id отправителя, текущее
состояние светофора). Светофор может взводить таймер, который через заданное время
отсылают заданное событие на заданный id. Отправка события - это помещение контейнера в
очередь событий для светофора, у каждого светофора очередь своя собственная. Светофоры
обрабатывают события параллельно, независимо от друг от друга. При этом каждый светофор
обрабатывает свои события последовательно, в том порядке, в каком они помещаются в очередь.
Светофор может получить информацию о текущем состоянии любого другого светофора
синхронно (не через событие).

<h3><b>Принципиальный алгоритм:</b></h3>
<h4><b>1. Определение приоритетного светофора:</b></h4>
   a. С помощью очереди сообщений:  
   - Каждый светофор отправляет всем светофорам запрос на приоритет вида: PRIORITY_REQUEST, id отправителя и длина очереди. 
   - Светофор-получатель сравнивает свою длину очереди с очередью отправителя и если она меньше отправляет подтверждение приоритета вида: PRIORITY_GRANTED, отправителя.
   - Каждый светофор проверяет свою очередь событий и суммирует уникальные подтверждения PRIORITY_GRANTED.
   - Как только, сумма приоритетов соответсвует количеству устройств в сети минус 1, светофор получает приоритет. 
   b. С помощью других светофоров:
   - Каждый светофор регулярно проверяет очереди других светофоров, как только очередь превышает пороговое значение, светофор-куратор подключает приоритет загруженному светофору.

<h4><b>2. Управление приоритетами.</b></h4>
   - Приоритетный светофор остается зеленым в течение определенного периода времени, зависящего от общего трафика, либо до полной очистки очереди автомобилей/пешеходов.
   - Когда приоритет автомобильного светофора заканчивается, он переключается на желтый (+1секунда), а затем на красный.
   - Когда приоритет пешеходного светофора заканчивается, он переключается на красный.
   - Приоритетный светофор выдает приоритеты другим светофорам из своего списка зависимостей. После окончания приоритета светофоры из списка зависимостей также теряю приоритет.
   - Любой светофор, в свою очередь, находится в списках зависимостей других светофоров и может быть наделен приоритетом с их стороны. Необходимыми условиями для этого являются: отсутсвие действующего приоритета, не нулевая очередь и статус -  on-line.
   - При получении приоритета, любой светофор может анулировать приоритет других светофоров, не из своего списка зависимостей. Ключевым условием для этого является превосходство очереди транспорта/пешеходов у данного светофора. Если очередь, вновь получившего приоритет светофора, окажется меньше других, он потеряет свой приоритет немедленно.  

<h4><b>3. Адаптация к изменениям в трафике.</b></h4>
   - Светофоры постоянно обмениваются данными о количестве автомобилей и пешеходов в своих очередях. Превышение пороговых значений трафика немедленно активирует приоритет у загруженного светофора и светофоров в его списке зависимостей.
   - Модуль управления светофором анализирует трафик и увеличивает время зеленой волны для максимальной пропускной способности загруженого светофора или группы светофоров.
