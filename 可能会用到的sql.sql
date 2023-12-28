"""
循环参数传错了，导致1min内重复储存了多条数据，现在需要删除

查询1min内重复出现的多条数据，

"""
SELECT eid, time, COUNT(*) as occurrences
FROM e_time_date_clone
WHERE date = '2023-12-09'
GROUP BY eid, time
HAVING COUNT(*) > 1;






下面这个会报错，
"""
mysql>
DEmysql> DELETE FROM e_time_date_clone
    -> WHERE (date, time, eid) IN (
    ->     SELECT date, time, eid
    ->     FROM e_time_date_clone
    ->     WHERE date = '2023-12-09'
    ->     GROUP BY date, time, eid
    ->     HAVING COUNT(*) > 1
    -> ) AND TIMESTAMPDIFF(MINUTE, CONCAT(date, ' ', time), CONCAT(date, ' ', time)) <= 1;
ERROR 1093 (HY000): You can't specify target table 'e_time_date_clone' for update in FROM clause

"""
DELETE FROM e_time_date_clone 
WHERE (date, time, eid) IN (
    SELECT date, time, eid
    FROM e_time_date_clone 
    WHERE date = '2023-12-09'
    GROUP BY date, time, eid
    HAVING COUNT(*) > 1
) AND TIMESTAMPDIFF(MINUTE, CONCAT(date, ' ', time), CONCAT(date, ' ', time)) <= 1;

"""
这个错误通常是由于 MySQL 的限制导致的，不允许在子查询中直接更新或删除目标表。为了解决这个问题，您可以使用临时表或子查询来处理。

以下是两种解决方法：

方法一：使用临时表

1. 创建一个临时表，将子查询的结果存储在其中：

```sql
CREATE TEMPORARY TABLE temp_table AS (
    SELECT date, time, eid
    FROM e_time_date_clone
    WHERE date = '2023-12-09'
    GROUP BY date, time, eid
    HAVING COUNT(*) > 1
);
```

2. 使用临时表来执行删除操作：

```sql
DELETE FROM e_time_date_clone
WHERE (date, time, eid) IN (
    SELECT date, time, eid
    FROM temp_table
) 
AND TIMESTAMPDIFF(MINUTE, CONCAT(date, ' ', time), CONCAT(date, ' ', time)) <= 1;
```

方法二：使用子查询

1. 使用子查询将要删除的记录的主键（例如 `id`）存储在一个临时表中：

```sql
CREATE TEMPORARY TABLE temp_table AS (
    SELECT id
    FROM e_time_date_clone
    WHERE date = '2023-12-09'
    GROUP BY date, time, eid
    HAVING COUNT(*) > 1
);
```

2. 使用子查询来执行删除操作：

```sql
DELETE FROM e_time_date_clone
WHERE id IN (
    SELECT id
    FROM temp_table
) 
AND TIMESTAMPDIFF(MINUTE, CONCAT(date, ' ', time), CONCAT(date, ' ', time)) <= 1;
```

请注意，在执行任何删除操作之前，请务必备份重要的数据，并确保已经明确了要删除的记录的条件，以避免意外删除错误的数据。
"""

CREATE TEMPORARY TABLE temp_table AS (
    SELECT date, time, eid
    FROM e_time_date_clone
    WHERE date = '2023-12-09'
    GROUP BY date, time, eid
    HAVING COUNT(*) > 1
);

DELETE FROM e_time_date_clone
WHERE (date, time, eid) IN (
    SELECT date, time, eid
    FROM temp_table
) 
AND TIMESTAMPDIFF(MINUTE, CONCAT(date, ' ', time), CONCAT(date, ' ', time)) <= 1;

DROP TABLE temp_table;

DROP TABLE e_time_date_clone;

"""
上面是clone表测试，下面是原表运行
"""


SELECT eid, time, COUNT(*) as occurrences
FROM e_time_date
WHERE date = '2023-12-09'
GROUP BY eid, time
HAVING COUNT(*) > 1;


CREATE TEMPORARY TABLE temp_table AS (
    SELECT date, time, eid
    FROM e_time_date
    WHERE date = '2023-12-09'
    GROUP BY date, time, eid
    HAVING COUNT(*) > 1
);

DELETE FROM e_time_date
WHERE (date, time, eid) IN (
    SELECT date, time, eid
    FROM temp_table
) 
AND TIMESTAMPDIFF(MINUTE, CONCAT(date, ' ', time), CONCAT(date, ' ', time)) <= 1;

DROP TABLE temp_table;