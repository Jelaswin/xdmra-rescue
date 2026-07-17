from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class EvaluationExperiment(Base):
    __tablename__ = "evaluation_experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String, nullable=False)
    module_type = Column(String, nullable=False)  # rescue, relief, shelter, priority
    algorithm_name = Column(String, nullable=False)
    scenario_count = Column(Integer, default=0)
    random_seed = Column(Integer, nullable=True)
    configuration_json = Column(JSON, nullable=True)
    status = Column(String, default="created")  # created, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    git_commit = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    results = relationship("EvaluationScenarioResult", back_populates="experiment", cascade="all, delete-orphan")
    metrics = relationship("EvaluationMetricSummary", back_populates="experiment", cascade="all, delete-orphan")


class EvaluationScenarioResult(Base):
    __tablename__ = "evaluation_scenario_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("evaluation_experiments.id"), nullable=False)
    scenario_reference = Column(String, nullable=False)
    algorithm_name = Column(String, nullable=False)
    module_type = Column(String, nullable=False)
    success = Column(Integer, default=0)  # boolean
    selected_resource_id = Column(Integer, nullable=True)
    selected_resource_name = Column(String, nullable=True)
    total_score = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    computation_time_ms = Column(Float, nullable=True)
    metrics_json = Column(JSON, nullable=True)
    explanation_available = Column(Integer, default=0)  # boolean
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    experiment = relationship("EvaluationExperiment", back_populates="results")


class EvaluationMetricSummary(Base):
    __tablename__ = "evaluation_metric_summaries"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("evaluation_experiments.id"), nullable=False)
    metric_name = Column(String, nullable=False)
    mean_value = Column(Float, nullable=True)
    median_value = Column(Float, nullable=True)
    minimum_value = Column(Float, nullable=True)
    maximum_value = Column(Float, nullable=True)
    standard_deviation = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    experiment = relationship("EvaluationExperiment", back_populates="metrics")