/**
 * @name Too many parameters
 * @description Functions with too many parameters can be hard to read and maintain.
 * @kind problem
 * @precision high
 * @problem.severity warning
 * @id js/too-many-params
 * @tags maintainability
 */
import javascript

from Function f
where f.getNumParameter() > 3
select f, "Function " + f.getName() + " has " + f.getNumParameter().toString() + " parameters, which is more than the allowed 3."