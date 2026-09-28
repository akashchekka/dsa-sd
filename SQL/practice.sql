-- SQLite

-- select * from departments;
-- select * from projects;
-- select * from employees;
-- select * from employee_projects;

-- create temp table emp as 
-- select * from employees 
-- where performance_rating = 5;

-- with CTE as (
--     select department_id, location from departments
--     where annual_budget < 3000000
-- )
-- select
--     e.employee_name, e.email, p.project_status
-- from employees e
-- inner join temp.emp tempp on tempp.employee_id = e.employee_id
-- inner join employee_projects ep on ep.employee_id = e.employee_id
-- inner join projects p on p.project_id = ep.project_id
-- inner join CTE cte on cte.department_id = e.department_id
-- where cte.location = 'Hyderabad';

-- 2nd Max budget

select MAX(budget) from projects
where budget < (select MAX(budget) from projects);

select budget as '2ndmax' from (
    select p.*, DENSE_RANK() over (
        order by budget desc
    ) as rank from projects p
)
where rank = 2;

-- DENSE_RANK()

select * from projects order by owning_department_id, budget;

select rank, budget, owning_department_id from (
    select 
        DENSE_RANK() OVER (
            partition by owning_department_id
            order by budget asc
        ) as rank, p.*
    from projects p
) as t
order by t.owning_department_id asc, t.budget desc;

-- Duplicate Entries

select owning_department_id, count(*) as 'cnt'
from projects
group by owning_department_id
having cnt > 1;

with ranked as (
    select p.*, ROW_NUMBER() OVER (
        partition by owning_department_id
        order by budget
    ) as row_rank
    from projects p
)
select row_rank, * from ranked where row_rank > 1;

-- Running Total

select owning_department_id, start_date, 
    SUM(budget) over (
        order by start_date
    ) as running_total
from projects;

select * from (
    select owning_department_id, start_date, DENSE_RANK() over (
        partition by owning_department_id
        order by start_date
    ) as rank
    from projects
) order by owning_department_id;

--- 

SELECT * FROM monthly_sales;

with revenue_history as (
    select LAG(revenue) OVER (
        order by month_start
    ) as prev_month_revenue,
    *
    from monthly_sales
)
select 
    revenue,
    prev_month_revenue,
    revenue - prev_month_revenue AS revenue_change,
    100.0 * (revenue - prev_month_revenue)/prev_month_revenue as 'percentage_change'
from revenue_history;

