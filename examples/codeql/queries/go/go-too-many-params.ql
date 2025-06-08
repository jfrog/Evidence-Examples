/**
 * @name Functions with too many parameters
 * @description Finds Go functions that have more than 3 parameters.
 * @kind problem
 * @problem.severity warning
 * @id go/too-many-parameters
 */
import go

from Function f
where f.getNumParameter() > 3
select f, "Function " + f.getName() + " has " + f.getNumParameter().toString() + " parameters, which is more than the allowed 3."
