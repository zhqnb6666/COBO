# database/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DOUBLE_PRECISION
from sqlalchemy.orm import relationship
from database.base import Base

class TACOProblem(Base):
    __tablename__ = 'taco_problems0_2'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text)
    starter_code = Column(Text, nullable=True)
    difficulty = Column(String)
    raw_tags = Column(Text)
    name = Column(String, nullable=True)
    source = Column(String)
    tags = Column(Text)
    skill_types = Column(Text)
    url = Column(String)
    expected_auxiliary_space = Column(String, nullable=True)
    time_limit = Column(String)
    date = Column(String)
    picture_num = Column(String)
    memory_limit = Column(String)
    expected_time_complexity = Column(String, nullable=True)
    fn_name = Column(String, nullable=True)
    is_tested = Column(Integer, default=0)
    is_valid = Column(Integer, default=0)
    test_repeat_time = Column(Integer, default=1)
    # Relationships
    solutions = relationship('Solution', back_populates='problem')
    valid_solutions = relationship('ValidSolution', back_populates='problem')
    input_outputs = relationship('InputOutput', back_populates='problem')


class Solution(Base):
    __tablename__ = 'solutions0_2'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey('public.taco_problems0_2.id'))
    solution_text = Column(Text)
    is_tested = Column(Integer, default=0)
    # Relationship
    problem = relationship('TACOProblem', back_populates='solutions')
    valid_solution = relationship('ValidSolution', back_populates='solution')


class ValidSolution(Base):
    __tablename__ = 'valid_solutions0_2'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey('public.taco_problems0_2.id'))
    solution_id = Column(Integer, ForeignKey('public.solutions0_2.id'))
    solution_text = Column(Text)
    run_time = Column(DOUBLE_PRECISION)
    test_iterations = Column(Integer, default=0)
    problem = relationship('TACOProblem', back_populates='valid_solutions')
    solution = relationship('Solution', back_populates='valid_solution')


class InputOutput(Base):
    __tablename__ = 'input_outputs0_2'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey('public.taco_problems0_2.id'))
    input_text = Column(Text)
    output_text = Column(Text)

    # Relationship
    problem = relationship('TACOProblem', back_populates='input_outputs')

