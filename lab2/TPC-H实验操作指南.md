# 实验二：PostgreSQL 创建、修改和导入 TPC-H 数据

## 1. 已验证环境

- 操作系统：macOS（Apple Silicon）
- DBMS：PostgreSQL 17.11（Homebrew）
- 数据库：`tpch`
- 数据文件：`/Applications/database/实验数据/csv/`
- 验证日期：2026-09-20

以下命令已在本机实际执行成功。目前 `tpch` 数据库已经建表并完成数据导入，因此不要再次执行“首次初始化”部分，否则会提示数据库、表或主键数据已经存在。查询验证部分可以重复执行。

## 2. 启动 PostgreSQL

在 macOS 终端执行：

```bash
brew services start postgresql@17
psql --version
```

预期输出（版本号的小版本以后可能不同）：

```text
Service `postgresql@17` already started
psql (PostgreSQL) 17.11 (Homebrew)
```

查看服务状态：

```bash
brew services list | grep postgresql
```

预期看到 `postgresql@17 started`。

## 3. 首次创建并连接数据库

> 本机已经完成此步骤，不要重复执行 `createdb tpch`。

首次初始化时使用：

```bash
createdb tpch
psql tpch
```

进入数据库后，提示符通常为：

```text
tpch=#
```

确认当前数据库：

```sql
SELECT current_database();
```

预期结果：

```text
 current_database
------------------
 tpch
(1 row)
```

## 4. 首次创建 8 张表

> 以下建表语句已经在本机执行成功，不要在当前 `tpch` 数据库中重复执行。

连接 `tpch` 后执行：

```sql
CREATE TABLE region (
    r_regionkey INTEGER NOT NULL,
    r_name      CHAR(25) NOT NULL,
    r_comment   VARCHAR(152)
);

CREATE TABLE nation (
    n_nationkey INTEGER NOT NULL,
    n_name      CHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment   VARCHAR(152)
);

CREATE TABLE part (
    p_partkey     INTEGER NOT NULL,
    p_name        VARCHAR(55) NOT NULL,
    p_mfgr        CHAR(25) NOT NULL,
    p_brand       CHAR(10) NOT NULL,
    p_type        VARCHAR(25) NOT NULL,
    p_size        INTEGER NOT NULL,
    p_container   CHAR(10) NOT NULL,
    p_retailprice DECIMAL(15,2) NOT NULL,
    p_comment     VARCHAR(23) NOT NULL
);

CREATE TABLE supplier (
    s_suppkey   INTEGER NOT NULL,
    s_name      CHAR(25) NOT NULL,
    s_address   VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone     CHAR(15) NOT NULL,
    s_acctbal   DECIMAL(15,2) NOT NULL,
    s_comment   VARCHAR(101) NOT NULL
);

CREATE TABLE partsupp (
    ps_partkey    INTEGER NOT NULL,
    ps_suppkey    INTEGER NOT NULL,
    ps_availqty   INTEGER NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment    VARCHAR(199) NOT NULL
);

CREATE TABLE customer (
    c_custkey    INTEGER NOT NULL,
    c_name       VARCHAR(25) NOT NULL,
    c_address    VARCHAR(40) NOT NULL,
    c_nationkey  INTEGER NOT NULL,
    c_phone      CHAR(15) NOT NULL,
    c_acctbal    DECIMAL(15,2) NOT NULL,
    c_mktsegment CHAR(10) NOT NULL,
    c_comment    VARCHAR(117) NOT NULL
);

CREATE TABLE orders (
    o_orderkey      INTEGER NOT NULL,
    o_custkey       INTEGER NOT NULL,
    o_orderstatus   CHAR(1) NOT NULL,
    o_totalprice    DECIMAL(15,2) NOT NULL,
    o_orderdate     DATE NOT NULL,
    o_orderpriority CHAR(15) NOT NULL,
    o_clerk         CHAR(15) NOT NULL,
    o_shippriority  INTEGER NOT NULL,
    o_comment       VARCHAR(79) NOT NULL
);

CREATE TABLE lineitem (
    l_orderkey      INTEGER NOT NULL,
    l_partkey       INTEGER NOT NULL,
    l_suppkey       INTEGER NOT NULL,
    l_linenumber    INTEGER NOT NULL,
    l_quantity      DECIMAL(15,2) NOT NULL,
    l_extendedprice DECIMAL(15,2) NOT NULL,
    l_discount      DECIMAL(15,2) NOT NULL,
    l_tax           DECIMAL(15,2) NOT NULL,
    l_returnflag    CHAR(1) NOT NULL,
    l_linestatus    CHAR(1) NOT NULL,
    l_shipdate      DATE NOT NULL,
    l_commitdate    DATE NOT NULL,
    l_receiptdate   DATE NOT NULL,
    l_shipinstruct  CHAR(25) NOT NULL,
    l_shipmode      CHAR(10) NOT NULL,
    l_comment       VARCHAR(44) NOT NULL
);
```

每条语句的预期输出：

```text
CREATE TABLE
```

检查表是否全部创建：

```sql
\dt
```

预期看到 8 张表：`region`、`nation`、`part`、`supplier`、`partsupp`、`customer`、`orders`、`lineitem`。

## 5. 首次添加主键和外键

> 以下约束已经添加，不要在当前数据库中重复执行。

```sql
ALTER TABLE region
    ADD PRIMARY KEY (r_regionkey);

ALTER TABLE nation
    ADD PRIMARY KEY (n_nationkey),
    ADD FOREIGN KEY (n_regionkey) REFERENCES region(r_regionkey);

ALTER TABLE part
    ADD PRIMARY KEY (p_partkey);

ALTER TABLE supplier
    ADD PRIMARY KEY (s_suppkey),
    ADD FOREIGN KEY (s_nationkey) REFERENCES nation(n_nationkey);

ALTER TABLE partsupp
    ADD PRIMARY KEY (ps_partkey, ps_suppkey),
    ADD FOREIGN KEY (ps_partkey) REFERENCES part(p_partkey),
    ADD FOREIGN KEY (ps_suppkey) REFERENCES supplier(s_suppkey);

ALTER TABLE customer
    ADD PRIMARY KEY (c_custkey),
    ADD FOREIGN KEY (c_nationkey) REFERENCES nation(n_nationkey);

ALTER TABLE orders
    ADD PRIMARY KEY (o_orderkey),
    ADD FOREIGN KEY (o_custkey) REFERENCES customer(c_custkey);

ALTER TABLE lineitem
    ADD PRIMARY KEY (l_orderkey, l_linenumber),
    ADD FOREIGN KEY (l_orderkey) REFERENCES orders(o_orderkey),
    ADD FOREIGN KEY (l_partkey, l_suppkey)
        REFERENCES partsupp(ps_partkey, ps_suppkey);
```

每条语句的预期输出：

```text
ALTER TABLE
```

本机实际验证结果为 8 个主键约束和 8 个外键约束。

## 6. 首次导入 CSV 数据

这里使用 `\copy`，文件由 `psql` 客户端读取，不需要修改 PostgreSQL 的服务器文件权限。必须按照外键依赖顺序导入。

> 当前数据库已经导入全部数据，不要重复执行，否则会出现主键重复错误。

```sql
\copy region FROM '/Applications/database/实验数据/csv/region.csv' WITH (FORMAT csv);
\copy nation FROM '/Applications/database/实验数据/csv/nation.csv' WITH (FORMAT csv);
\copy part FROM '/Applications/database/实验数据/csv/part.csv' WITH (FORMAT csv);
\copy supplier FROM '/Applications/database/实验数据/csv/supplier.csv' WITH (FORMAT csv);
\copy customer FROM '/Applications/database/实验数据/csv/customer.csv' WITH (FORMAT csv);
\copy partsupp FROM '/Applications/database/实验数据/csv/partsupp.csv' WITH (FORMAT csv);
\copy orders FROM '/Applications/database/实验数据/csv/orders.csv' WITH (FORMAT csv);
\copy lineitem FROM '/Applications/database/实验数据/csv/lineitem.csv' WITH (FORMAT csv);
```

本机实际输出：

```text
COPY 5
COPY 25
COPY 2000
COPY 100
COPY 1500
COPY 8000
COPY 15000
COPY 60175
```

这些数字分别对应上面 8 条导入命令。

## 7. 验证各表行数

这部分可以重复执行：

```sql
SELECT 'region' AS table_name, COUNT(*) AS row_count FROM region
UNION ALL SELECT 'nation', COUNT(*) FROM nation
UNION ALL SELECT 'supplier', COUNT(*) FROM supplier
UNION ALL SELECT 'customer', COUNT(*) FROM customer
UNION ALL SELECT 'part', COUNT(*) FROM part
UNION ALL SELECT 'partsupp', COUNT(*) FROM partsupp
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'lineitem', COUNT(*) FROM lineitem;
```

本机实际结果，也是作业要求的预期结果：

```text
 table_name | row_count
------------+----------
 region     |         5
 nation     |        25
 supplier   |       100
 customer   |      1500
 part       |      2000
 partsupp   |      8000
 orders     |     15000
 lineitem   |     60175
(8 rows)
```

## 8. 简单 SELECT 查询

```sql
SELECT r_regionkey, r_name
FROM region
ORDER BY r_regionkey;
```

预期返回 5 个地区：`AFRICA`、`AMERICA`、`ASIA`、`EUROPE`、`MIDDLE EAST`。

再查询订单总数和平均金额：

```sql
SELECT COUNT(*) AS order_count,
       ROUND(AVG(o_totalprice), 2) AS avg_totalprice
FROM orders;
```

本机实际结果：

```text
 order_count | avg_totalprice
-------------+---------------
       15000 |     141826.46
(1 row)
```

## 9. JOIN 查询

查询国家及所属地区：

```sql
SELECT n.n_name, r.r_name
FROM nation AS n
JOIN region AS r
  ON n.n_regionkey = r.r_regionkey
ORDER BY n.n_nationkey
LIMIT 5;
```

本机实际结果：

```text
          n_name           |          r_name
---------------------------+---------------------------
 ALGERIA                   | AFRICA
 ARGENTINA                 | AMERICA
 BRAZIL                    | AMERICA
 CANADA                    | AMERICA
 EGYPT                     | MIDDLE EAST
(5 rows)
```

再执行一个订单、客户和国家三表连接：

```sql
SELECT o.o_orderkey,
       c.c_name,
       n.n_name AS nation,
       o.o_totalprice,
       o.o_orderdate
FROM orders AS o
JOIN customer AS c ON o.o_custkey = c.c_custkey
JOIN nation AS n ON c.c_nationkey = n.n_nationkey
ORDER BY o.o_orderkey
LIMIT 10;
```

预期返回 10 条订单，并显示对应客户、国家、金额和日期。本机第一条结果的订单号为 `1`，客户为 `Customer#000000370`，国家为 `JAPAN`，金额为 `172799.49`，日期为 `1996-01-02`。

## 10. 实验截图建议

实验报告中依次保留：

1. `psql --version` 和 PostgreSQL 服务状态。
2. `\dt` 显示 8 张表。
3. `ALTER TABLE` 成功输出，或用 `\d 表名` 展示主外键。
4. 8 条 `\copy` 的 `COPY 行数` 输出。
5. 8 张表的行数验证结果。
6. 简单 SELECT 和 JOIN 查询结果。

因为当前数据库已经初始化，重新进入数据库并截图可以使用：

```bash
psql tpch
```

进入后执行：

```sql
\dt
\d lineitem
```

退出 `psql`：

```sql
\q
```

## 11. 常见错误

- `database "tpch" already exists`：说明数据库已经创建，不需要再次运行 `createdb tpch`。
- `relation "region" already exists`：说明表已经创建，不要重复执行建表语句。
- `duplicate key value violates unique constraint`：说明数据已经导入，不要再次执行 `\copy`。
- `violates foreign key constraint`：通常是导入顺序错误，必须使用本文第 6 节的顺序。
- 路径不存在：确认数据仍位于 `/Applications/database/实验数据/csv/`。
