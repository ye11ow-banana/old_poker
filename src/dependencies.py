from typing import Annotated

from fastapi import Depends

from unitofwork import IUnitOfWork, UnitOfWork

UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]
