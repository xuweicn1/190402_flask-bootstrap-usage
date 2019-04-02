import pymysql

con = pymysql.connect('localhost', 'root', 'password', 'myflaskapp')
cur = con.cursor()


def creat():
  with con:
    sql = '''CREATE TABLE articles(
            id INT(11) AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) ,
            author VARCHAR(255) ,
            body  TEXT,
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'''

    cur.execute("DROP TABLE IF EXISTS articles")
    cur.execute(sql)


# def in_one():
#   with con:
#     sql = "INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)"
#     cur.execute(sql, (1, 2, 3)


if __name__ == "__main__":
    # creat()
  with con:
    result = cur.execute("SELECT * FROM articles")
    print(result)

  # creat()
  # in_one()
