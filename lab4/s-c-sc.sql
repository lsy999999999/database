-- "sc"."course" definition

-- Drop table

-- DROP TABLE "sc"."course";

CREATE TABLE "sc"."course" (
	"cno" character(5 char) NOT NULL,
	"cname" character varying(40 char) NOT NULL,
	"ccredit" smallint NULL,
	"cpno" character(5 char) NULL,
	CONSTRAINT "course_pkey" PRIMARY KEY (cno),
	CONSTRAINT "course_cpno_fkey" FOREIGN KEY (cpno) REFERENCES sc.course(cno)
);

-- "sc"."student" definition

-- Drop table

-- DROP TABLE "sc"."student";

CREATE TABLE "sc"."student" (
	"sno" character(8 char) NOT NULL,
	"sname" character varying(20 char) NULL,
	"ssex" character(6 char) NULL,
	"sbirthdate" date NULL,
	"smajor" character varying(40 char) NULL,
	CONSTRAINT "student_pkey" PRIMARY KEY (sno),
	CONSTRAINT "student_sname_key" UNIQUE (sname)
);

-- "sc"."sc" definition

-- Drop table

-- DROP TABLE "sc"."sc";

CREATE TABLE "sc"."sc" (
	"sno" character(8 char) NOT NULL,
	"cno" character(5 char) NOT NULL,
	"grade" smallint NULL,
	"semester" character(5 char) NULL,
	"teachingclass" character(8 char) NULL,
	CONSTRAINT "sc_pkey" PRIMARY KEY (sno, cno)
);


-- "sc"."sc" foreign keys

ALTER TABLE "sc"."sc" ADD CONSTRAINT "sc_cno_fkey" FOREIGN KEY (cno) REFERENCES sc.course(cno);
ALTER TABLE "sc"."sc" ADD CONSTRAINT "sc_sno_fkey" FOREIGN KEY (sno) REFERENCES sc.student(sno);

INSERT INTO "sc"."student" ("sno","sname","ssex","sbirthdate","smajor") VALUES
	 ('20180001','李勇','男     ','''2000-03-08 00:00:00''','信息安全'),
	 ('20180002','刘晨','女     ','''1999-09-01 00:00:00''','计算机科学与技术'),
	 ('20180003','王敏','女     ','''2001-08-01 00:00:00''','计算机科学与技术'),
	 ('20180004','张立','男     ','''2000-01-08 00:00:00''','计算机科学与技术'),
	 ('20180205','陈新奇','男     ','''2001-11-01 00:00:00''','信息管理与信息系统'),
	 ('20180306','赵明','男     ','''2000-06-12 00:00:00''','数据科学与大数据技术'),
	 ('20180307','王佳佳','女     ','''2001-12-07 00:00:00''','数据科学与大数据技术');


INSERT INTO "sc"."course" ("cno","cname","ccredit","cpno") VALUES
	 ('81001','程序设计基础与C语言',4,NULL),
	 ('81002','数据结构',4,'81001'),
	 ('81003','数据库系统概论',4,'81002'),
	 ('81004','信息系统概论',4,'81003'),
	 ('81005','操作系统',4,'81001'),
	 ('81006','Python语言',3,'81002'),
	 ('81007','离散数学',4,NULL),
	 ('81008','大数据技术概论',4,'81003');


INSERT INTO "sc"."sc" ("sno","cno","grade","semester","teachingclass") VALUES
	 ('20180001','81001',85,'20192','81001-01'),
	 ('20180001','81002',96,'20201','81002-01'),
	 ('20180001','81003',87,'20202','81003-01'),
	 ('20180002','81001',80,'20192','81001-02'),
	 ('20180002','81002',98,'20201','81002-01'),
	 ('20180002','81003',71,'20202','81003-02'),
	 ('20180003','81001',81,'20192','81001-01'),
	 ('20180003','81002',76,'20201','81002-02'),
	 ('20180004','81001',56,'20192','81001-02'),
	 ('20180004','81003',97,'20201','81002-02'),
	 ('20180205','81003',68,'20202','81003-01');