# Código SQL
```sql
-- Criação da base de dados (opcional)
CREATE DATABASE IF NOT EXISTS crm_db;
USE crm_db;

-- 1. Tabela companies (auto-relacionada)
CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(255) NOT NULL,
    campany_id INT NULL,
    CONSTRAINT fk_companies_parent 
        FOREIGN KEY (campany_id) REFERENCES companies(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 2. Tabela users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company INT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('EMPLOYEE', 'COMPANY', 'MANAGER') NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    CONSTRAINT fk_users_company 
        FOREIGN KEY (company) REFERENCES companies(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 3. Tabela customers
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    notes VARCHAR(255),
    cel VARCHAR(64),
    email VARCHAR(64),
    birth DATETIME,
    address VARCHAR(64),
    company_id INT NULL,
    CONSTRAINT fk_customers_company 
        FOREIGN KEY (company_id) REFERENCES companies(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4. Tabela product
CREATE TABLE product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    price VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- 5. Tabela plugins
CREATE TABLE plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- 6. Tabela pipelines
CREATE TABLE pipelines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note VARCHAR(255),
    date DATETIME,
    step ENUM(
        'PROPSECTING',
        'PREPARATION',
        'APPROACH',
        'PRESENTATION',
        'HANDLING_OBJECTIONS',
        'CLOSING',
        'FOLLOW_UP'
    ) NOT NULL,
    customer_id INT NULL,
    employee_id INT NULL,
    CONSTRAINT fk_pipelines_customer 
        FOREIGN KEY (customer_id) REFERENCES customers(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_pipelines_employee 
        FOREIGN KEY (employee_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 7. Tabela sale_product
CREATE TABLE sale_product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quantidade INT NOT NULL,
    sale_id INT NULL,
    product_id INT NULL,
    CONSTRAINT fk_sale_product_sale 
        FOREIGN KEY (sale_id) REFERENCES pipelines(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sale_product_product 
        FOREIGN KEY (product_id) REFERENCES product(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. Tabela company_plugin
CREATE TABLE company_plugin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    plugin_id INT NOT NULL,
    CONSTRAINT fk_cp_company 
        FOREIGN KEY (company_id) REFERENCES companies(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cp_plugin 
        FOREIGN KEY (plugin_id) REFERENCES plugins(id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

```