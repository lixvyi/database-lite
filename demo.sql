CREATE TABLE student(id INT, name VARCHAR(20), age INT);
INSERT INTO student(id,name,age) VALUES (1,'Alice',20);
INSERT INTO student(id,name,age) VALUES (2,'Bob',17);
SELECT name,age FROM student WHERE age >= 18 ORDER BY age DESC;
UPDATE student SET age = age + 1 WHERE id = 2;
DELETE FROM student WHERE id = 1;
