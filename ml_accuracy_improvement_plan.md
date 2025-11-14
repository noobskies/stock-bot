# Implementation Plan: ML Accuracy Measurement & Improvement System

## Overview

Build a comprehensive ML performance monitoring and improvement system that tracks model accuracy in real-time, optimizes training through hyperparameter tuning and cross-validation, and automatically retrains models when performance degrades.

This system addresses the critical need for maintaining high-quality predictions in live trading by:

1. **Live Monitoring** - Continuously tracking prediction accuracy against actual outcomes during paper/live trading
2. **Advanced Training** - Improving base model accuracy through systematic hyperparameter optimization and robust validation
3. **Automatic Retraining** - Detecting model degradation and triggering retraining workflows automatically
4. **Performance Analytics** - Providing comprehensive metrics visualization and analysis tools

The implementation integrates seamlessly with existing ML infrastructure (model_trainer.py, predictor.py, ensemble.py) and database repositories (prediction_repository.py) while adding new capabilities for performance tracking, model optimization, and automated maintenance.

## Types

New type definitions for performance tracking, model versioning, and training experiments.

```python
# src/bot_types/ml_types.py (NEW FILE)

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class ModelStatus(Enum):
    """Model lifecycle status."""
    TRAINING = "training"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ARCHIVED = "archived"


class PerformanceMetric(Enum):
    """Available performance metrics."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    DIRECTIONAL_ACCURACY = "directional_accuracy"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    SHARPE_RATIO = "sharpe_ratio"


@dataclass
class ModelVersion:
    """Track different versions of trained models."""
    version_id: str
    model_type: str  # "LSTM", "RandomForest", "Ensemble"
    model_path: str
    hyperparameters: Dict[str, Any]
    training_metrics: Dict[str, float]
    training_date: datetime
    status: ModelStatus
    data_version: str  # Hash of training data
    performance_history: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceWindow:
    """Rolling window of prediction performance."""
    window_size: int  # Number of predictions
    predictions_count: int
    correct_predictions: int
    accuracy: float
    confidence_avg: float
    start_time: datetime
    end_time: datetime
    metrics: Dict[str, float]


@dataclass
class TrainingExperiment:
    """Track hyperparameter tuning experiments."""
    experiment_id: str
    model_type: str
    hyperparameters: Dict[str, Any]
    cv_scores: List[float]
    mean_cv_score: float
    std_cv_score: float
    training_time_seconds: float
    test_metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    created_at: datetime
    notes: str = ""


@dataclass
class RetrainingTrigger:
    """Criteria for triggering model retraining."""
    trigger_type: str  # "accuracy_drop", "time_based", "data_drift", "manual"
    threshold_value: Optional[float]
    current_value: Optional[float]
    triggered_at: datetime
    reason: str
```

## Files

Comprehensive file creation and modification plan covering monitoring, optimization, and automation.

### New Files to Create

1. **src/ml/performance_monitor.py** (~350 lines)

   - Purpose: Real-time performance tracking and degradation detection
   - Classes: PerformanceMonitor
   - Key methods: track_prediction_outcome(), calculate_rolling_metrics(), detect_degradation()

2. **src/ml/hyperparameter_tuner.py** (~400 lines)

   - Purpose: Systematic hyperparameter optimization using grid/random search
   - Classes: HyperparameterTuner
   - Key methods: grid_search(), random_search(), bayesian_optimization(), cross_validate()

3. **src/ml/model_optimizer.py** (~300 lines)

   - Purpose: Feature selection, engineering, and model architecture optimization
   - Classes: ModelOptimizer
   - Key methods: feature_selection(), optimize_architecture(), ensemble_weights_optimization()

4. **src/ml/retraining_manager.py** (~450 lines)

   - Purpose: Automated retraining workflows and model versioning
   - Classes: RetrainingManager
   - Key methods: check_retraining_triggers(), execute_retraining(), rollback_model(), version_model()

5. **src/ml/model_registry.py** (~250 lines)

   - Purpose: Model versioning, storage, and lifecycle management
   - Classes: ModelRegistry
   - Key methods: register_model(), promote_to_production(), archive_model(), compare_models()

6. **src/database/repositories/ml_performance_repository.py** (~200 lines)

   - Purpose: Database operations for performance tracking
   - Classes: MLPerformanceRepository
   - Key methods: save_performance_window(), get_recent_performance(), save_experiment(), get_model_versions()

7. **src/bot_types/ml_types.py** (~150 lines)

   - Purpose: Type definitions for ML performance system
   - New types: ModelVersion, PerformanceWindow, TrainingExperiment, RetrainingTrigger, ModelStatus, PerformanceMetric

8. **tests/test_performance_monitor.py** (~200 lines)

   - Purpose: Unit tests for performance monitoring
   - Tests: Rolling metrics calculation, degradation detection, prediction outcome tracking

9. **tests/test_hyperparameter_tuner.py** (~250 lines)

   - Purpose: Unit tests for hyperparameter optimization
   - Tests: Grid search, cross-validation, experiment tracking

10. **tests/test_retraining_manager.py** (~200 lines)
    - Purpose: Unit tests for retraining automation
    - Tests: Trigger detection, retraining workflow, rollback functionality

### Existing Files to Modify

1. **src/ml/model_trainer.py** (~350 lines currently)

   - Add: save_experiment() method to track training runs
   - Add: load_best_model() method to load optimal model from experiments
   - Modify: train_model() to accept hyperparameters dict and log experiments
   - Add: cross_validation() method for robust validation

2. **src/ml/predictor.py** (~300 lines currently)

   - Add: Integration with PerformanceMonitor to track predictions
   - Modify: predict_next_day() to log predictions for accuracy tracking
   - Add: get_confidence_calibration() method for calibration analysis

3. **src/ml/ensemble.py** (~400 lines currently)

   - Add: dynamic_weight_adjustment() based on recent performance
   - Modify: ensemble_predict() to log ensemble performance
   - Add: Performance-based model selection

4. **src/database/schema.py** (~200 lines currently)

   - Add: ModelVersion table for version tracking
   - Add: PerformanceWindow table for rolling metrics
   - Add: TrainingExperiment table for optimization history
   - Add: RetrainingLog table for automation audit trail

5. **src/database/db_manager.py** (~350 lines currently)

   - Add: ml_performance property for MLPerformanceRepository
   - Add: Initialization of new repository in constructor

6. **src/orchestrators/trading_cycle.py** (~280 lines currently)

   - Add: Integration with PerformanceMonitor after each prediction
   - Add: Check for retraining triggers at end of cycle

7. **config/config.yaml** (~50 lines currently)

   - Add: ml.performance_monitoring section with thresholds
   - Add: ml.hyperparameter_tuning section with search parameters
   - Add: ml.retraining section with trigger criteria

8. **src/dashboard/app.py** (~800 lines currently)
   - Add: /api/ml/performance endpoint for metrics
   - Add: /api/ml/experiments endpoint for tuning history
   - Add: /api/ml/models endpoint for version management
   - Add: /api/ml/retrain endpoint to trigger manual retraining

### Files for Dashboard Visualization (Optional - Phase 2)

9. **dashboard/src/pages/MLPerformancePage.tsx** (NEW - React dashboard)
   - Purpose: ML performance visualization dashboard
   - Components: Performance charts, model comparison, experiment results

## Functions

Detailed breakdown of new and modified functions across all modules.

### New Functions

**src/ml/performance_monitor.py**:

- `__init__(window_size, degradation_threshold, min_predictions)` - Initialize monitor with configuration
- `track_prediction_outcome(prediction, actual_price, actual_direction)` - Record prediction vs actual
- `calculate_rolling_metrics(window_size)` - Compute metrics over rolling window
- `detect_degradation()` - Check if performance below threshold → Returns: bool, reason
- `get_performance_summary(days)` - Aggregate performance over time period
- `get_confidence_calibration()` - Analyze prediction confidence vs actual accuracy
- `export_performance_report(filepath)` - Generate CSV/JSON performance report
- `reset_metrics()` - Clear tracked predictions (for new model version)

**src/ml/hyperparameter_tuner.py**:

- `__init__(model_type, base_params, search_space)` - Initialize tuner with search configuration
- `grid_search(X_train, y_train, cv_folds)` - Exhaustive grid search → Returns: best_params, all_results
- `random_search(X_train, y_train, n_iterations, cv_folds)` - Random sampling search
- `bayesian_optimization(X_train, y_train, n_iterations)` - Bayesian hyperparameter optimization
- `cross_validate(params, X_train, y_train, cv_folds)` - K-fold cross-validation → Returns: cv_scores, metrics
- `save_experiment(experiment_data)` - Persist experiment to database
- `get_best_experiment()` - Retrieve best performing experiment → Returns: TrainingExperiment
- `visualize_experiments(metric)` - Plot experiment results comparison
- `get_search_space_config(model_type)` - Define parameter search ranges

**src/ml/model_optimizer.py**:

- `__init__(feature_engineer, predictor)` - Initialize with existing components
- `feature_selection(X, y, method, k)` - Select top k features → Returns: selected_features, importance_scores
- `optimize_architecture(X_train, y_train)` - Find optimal LSTM architecture (layers, units)
- `ensemble_weights_optimization(predictions_list, y_true)` - Optimize ensemble weights
- `analyze_feature_importance(model, feature_names)` - Comprehensive feature analysis
- `suggest_improvements()` - Analyze current model and suggest optimizations → Returns: recommendations list

**src/ml/retraining_manager.py**:

- `__init__(monitor, trainer, registry, config)` - Initialize with dependencies
- `check_retraining_triggers()` - Evaluate all trigger conditions → Returns: bool, trigger_reasons
- `execute_retraining(trigger_type)` - Full retraining workflow → Returns: new_model_version
- `schedule_retraining(schedule_type)` - Set up periodic retraining (daily/weekly/monthly)
- `rollback_model(version_id)` - Revert to previous model version
- `version_model(model_path, metrics, hyperparameters)` - Create new model version entry
- `compare_model_versions(version_ids)` - Performance comparison between versions
- `cleanup_old_versions(keep_n)` - Archive old model versions, keep best N

**src/ml/model_registry.py**:

- `__init__(db_manager)` - Initialize registry with database
- `register_model(model_version)` - Add new model to registry → Returns: version_id
- `promote_to_production(version_id)` - Set model as active production model
- `archive_model(version_id)` - Move model to archived status
- `get_active_model(model_type)` - Retrieve current production model
- `get_model_history(model_type, limit)` - List all versions for model type
- `compare_models(version_id_1, version_id_2)` - Side-by-side comparison
- `export_model(version_id, export_path)` - Export model with metadata

**src/database/repositories/ml_performance_repository.py**:

- `save_performance_window(window_data)` - Persist PerformanceWindow to database
- `get_recent_performance(model_type, days)` - Query recent performance metrics
- `save_experiment(experiment_data)` - Store TrainingExperiment results
- `get_best_experiments(model_type, metric, limit)` - Retrieve top experiments
- `save_model_version(model_version)` - Persist ModelVersion entry
- `get_model_versions(model_type, status)` - Query models by type and status
- `save_retraining_log(trigger, outcome)` - Audit log for retraining events
- `get_retraining_history(days)` - Query past retraining events

### Modified Functions

**src/ml/model_trainer.py**:

- `train_model()` - MODIFY: Add experiment tracking, accept hyperparameters dict, log to MLPerformanceRepository
- `evaluate_model()` - MODIFY: Return extended metrics including confidence calibration
- `save_model()` - MODIFY: Integrate with ModelRegistry for versioning
- `build_lstm_model()` - MODIFY: Accept architecture parameters for optimization
- ADD: `cross_validate(X, y, cv_folds)` - K-fold cross-validation for robust evaluation
- ADD: `save_experiment(hyperparameters, metrics)` - Log experiment to database

**src/ml/predictor.py**:

- `predict_next_day()` - MODIFY: Integrate with PerformanceMonitor to log prediction
- `predict_batch()` - MODIFY: Track batch predictions for accuracy analysis
- ADD: `get_confidence_calibration()` - Analyze calibration of confidence scores
- ADD: `get_prediction_history(days)` - Retrieve recent predictions with outcomes

**src/ml/ensemble.py**:

- `ensemble_predict()` - MODIFY: Log ensemble predictions, check for weight adjustment
- ADD: `dynamic_weight_adjustment()` - Adjust weights based on recent model performance
- ADD: `get_model_contributions()` - Analyze which models contribute most to predictions

**src/orchestrators/trading_cycle.py**:

- `_process_symbol()` - MODIFY: Add performance tracking integration after prediction
- `run()` - MODIFY: Check retraining triggers at end of trading cycle

## Classes

Detailed specification of new classes and their responsibilities.

### New Classes

**PerformanceMonitor** (src/ml/performance_monitor.py)

```python
class PerformanceMonitor:
    """
    Real-time ML model performance monitoring.

    Tracks predictions vs actual outcomes, calculates rolling metrics,
    and detects model degradation.
    """

    def __init__(
        self,
        window_size: int = 50,
        degradation_threshold: float = 0.55,
        min_predictions: int = 20,
        db_manager: DatabaseManager
    )

    # Key Methods:
    - track_prediction_outcome()
    - calculate_rolling_metrics()
    - detect_degradation()
    - get_performance_summary()
    - get_confidence_calibration()

    # Attributes:
    - prediction_buffer: List[Dict]  # Recent predictions
    - rolling_accuracy: float
    - degradation_detected: bool
```

**HyperparameterTuner** (src/ml/hyperparameter_tuner.py)

```python
class HyperparameterTuner:
    """
    Systematic hyperparameter optimization for ML models.

    Supports grid search, random search, and Bayesian optimization
    with k-fold cross-validation.
    """

    def __init__(
        self,
        model_type: str,  # "LSTM" or "RandomForest"
        base_params: Dict[str, Any],
        search_space: Dict[str, List[Any]],
        db_manager: DatabaseManager
    )

    # Key Methods:
    - grid_search()
    - random_search()
    - bayesian_optimization()
    - cross_validate()
    - save_experiment()

    # Attributes:
    - experiments: List[TrainingExperiment]
    - best_params: Dict[str, Any]
    - best_score: float
```

**ModelOptimizer** (src/ml/model_optimizer.py)

```python
class ModelOptimizer:
    """
    Model architecture and feature optimization.

    Performs feature selection, architecture search, and
    ensemble weight optimization.
    """

    def __init__(
        self,
        feature_engineer: FeatureEngineer,
        predictor: LSTMPredictor
    )

    # Key Methods:
    - feature_selection()
    - optimize_architecture()
    - ensemble_weights_optimization()
    - analyze_feature_importance()

    # Attributes:
    - selected_features: List[str]
    - optimal_architecture: Dict[str, Any]
```

**RetrainingManager** (src/ml/retraining_manager.py)

```python
class RetrainingManager:
    """
    Automated model retraining orchestration.

    Monitors triggers, executes retraining workflows,
    manages model versions, and handles rollbacks.
    """

    def __init__(
        self,
        performance_monitor: PerformanceMonitor,
        model_trainer: LSTMModelTrainer,
        model_registry: ModelRegistry,
        config: Dict[str, Any],
        db_manager: DatabaseManager
    )

    # Key Methods:
    - check_retraining_triggers()
    - execute_retraining()
    - schedule_retraining()
    - rollback_model()
    - version_model()

    # Attributes:
    - retraining_in_progress: bool
    - last_retrain_date: datetime
    - active_triggers: List[RetrainingTrigger]
```

**ModelRegistry** (src/ml/model_registry.py)

```python
class ModelRegistry:
    """
    Model version management and lifecycle tracking.

    Maintains registry of all model versions, handles
    promotion to production, and enables rollback.
    """

    def __init__(self, db_manager: DatabaseManager)

    # Key Methods:
    - register_model()
    - promote_to_production()
    - archive_model()
    - get_active_model()
    - compare_models()

    # Attributes:
    - models: Dict[str, List[ModelVersion]]
    - active_versions: Dict[str, str]  # model_type -> version_id
```

**MLPerformanceRepository** (src/database/repositories/ml_performance_repository.py)

```python
class MLPerformanceRepository(BaseRepository):
    """
    Database operations for ML performance tracking.

    Handles persistence of performance windows, experiments,
    model versions, and retraining logs.
    """

    def __init__(self, session_factory)

    # Key Methods:
    - save_performance_window()
    - get_recent_performance()
    - save_experiment()
    - get_best_experiments()
    - save_model_version()

    # Inherits from: BaseRepository (session management)
```

### Modified Classes

**LSTMModelTrainer** (src/ml/model_trainer.py)

- ADD attribute: experiment_tracker: MLPerformanceRepository
- ADD method: cross_validate()
- ADD method: save_experiment()
- MODIFY method: train_model() - add experiment logging
- MODIFY method: save_model() - integrate with ModelRegistry

**LSTMPredictor** (src/ml/predictor.py)

- ADD attribute: performance_monitor: PerformanceMonitor
- ADD method: get_confidence_calibration()
- ADD method: get_prediction_history()
- MODIFY method: predict_next_day() - add performance tracking

**EnsemblePredictor** (src/ml/ensemble.py)

- ADD attribute: performance_monitor: PerformanceMonitor
- ADD method: dynamic_weight_adjustment()
- ADD method: get_model_contributions()
- MODIFY method: ensemble_predict() - add performance logging

**TradingCycleOrchestrator** (src/orchestrators/trading_cycle.py)

- ADD attribute: retraining_manager: RetrainingManager
- MODIFY method: \_process_symbol() - integrate performance tracking
- MODIFY method: run() - check retraining triggers

## Dependencies

Package requirements and integration specifications.

### New Python Packages

Add to requirements.txt:

```txt
# Hyperparameter Optimization
scikit-optimize==0.9.0       # Bayesian optimization
optuna==3.4.0                # Modern hyperparameter tuning framework

# Model Persistence & Versioning
joblib==1.3.2                # Already installed, no change needed
mlflow==2.8.1                # Optional: Experiment tracking (advanced)

# Performance Monitoring
seaborn==0.13.0              # Visualization for performance analysis
plotly==5.18.0               # Interactive performance charts

# Enhanced ML Utilities
imbalanced-learn==0.11.0    # Handle class imbalance in training
shap==0.43.0                 # Model interpretability (optional)
```

### Existing Package Updates

No version changes required for:

- TensorFlow 2.19.1 (already current)
- scikit-learn 1.3.2 (already current)
- pandas 2.1.3 (already current)
- numpy 1.26.2 (already current)

### Internal Dependencies

Integration points with existing modules:

- Uses: src/ml/model_trainer.py (training workflows)
- Uses: src/ml/predictor.py (prediction tracking)
- Uses: src/ml/ensemble.py (ensemble performance)
- Uses: src/database/db_manager.py (data persistence)
- Uses: src/database/repositories/prediction_repository.py (prediction history)
- Uses: src/bot_types/trading_types.py (existing types)
- Uses: config/config.yaml (configuration)

### Database Schema Changes

New tables required (add to src/database/schema.py):

```python
class ModelVersion(Base):
    __tablename__ = 'model_versions'

    id = Column(Integer, primary_key=True)
    version_id = Column(String(50), unique=True, nullable=False)
    model_type = Column(String(50), nullable=False)
    model_path = Column(String(255), nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    training_metrics = Column(JSON, nullable=False)
    training_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # TRAINING, ACTIVE, DEGRADED, ARCHIVED
    data_version = Column(String(50), nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class PerformanceWindow(Base):
    __tablename__ = 'performance_windows'

    id = Column(Integer, primary_key=True)
    model_version_id = Column(String(50), nullable=False)
    window_size = Column(Integer, nullable=False)
    predictions_count = Column(Integer, nullable=False)
    correct_predictions = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    confidence_avg = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    metrics = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingExperiment(Base):
    __tablename__ = 'training_experiments'

    id = Column(Integer, primary_key=True)
    experiment_id = Column(String(50), unique=True, nullable=False)
    model_type = Column(String(50), nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    cv_scores = Column(JSON, nullable=False)
    mean_cv_score = Column(Float, nullable=False)
    std_cv_score = Column(Float, nullable=False)
    training_time_seconds = Column(Float, nullable=False)
    test_metrics = Column(JSON, nullable=False)
    feature_importance = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class RetrainingLog(Base):
    __tablename__ = 'retraining_logs'

    id = Column(Integer, primary_key=True)
    trigger_type = Column(String(50), nullable=False)
    threshold_value = Column(Float)
    current_value = Column(Float)
    triggered_at = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    old_model_version = Column(String(50))
    new_model_version = Column(String(50))
    retraining_success = Column(Boolean, nullable=False)
    retraining_time_seconds = Column(Float)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Testing

Comprehensive testing strategy for all new components.

### Unit Tests

**test_performance_monitor.py**:

```python
def test_track_prediction_outcome_correct()
def test_track_prediction_outcome_incorrect()
def test_calculate_rolling_metrics()
def test_degradation_detection_triggers()
def test_degradation_detection_no_trigger()
def test_confidence_calibration()
def test_performance_summary()
def test_reset_metrics()
```

**test_hyperparameter_tuner.py**:

```python
def test_grid_search_all_combinations()
def test_random_search_sampling()
def test_cross_validate_kfolds()
def test_save_experiment()
def test_get_best_experiment()
def test_search_space_config()
def test_bayesian_optimization()
```

**test_model_optimizer.py**:

```python
def test_feature_selection_top_k()
def test_optimize_architecture()
def test_ensemble_weights_optimization()
def test_analyze_feature_importance()
def test_suggest_improvements()
```

**test_retraining_manager.py**:

```python
def test_check_triggers_accuracy_drop()
def test_check_triggers_time_based()
def test_execute_retraining_workflow()
def test_rollback_model()
def test_version_model()
def test_cleanup_old_versions()
```

**test_model_registry.py**:

```python
def test_register_model()
def test_promote_to_production()
def test_archive_model()
def test_get_active_model()
def test_compare_models()
def test_get_model_history()
```

**test_ml_performance_repository.py**:

```python
def test_save_performance_window()
def test_get_recent_performance()
def test_save_experiment()
def test_get_best_experiments()
def test_save_model_version()
def test_get_model_versions()
```

### Integration Tests

**test_ml_performance_integration.py**:

```python
def test_end_to_end_performance_tracking()
    # Make predictions → Track outcomes → Calculate metrics → Detect degradation

def test_hyperparameter_tuning_workflow()
    # Define search space → Run grid search → Save experiments → Apply best params

def test_retraining_workflow()
    # Trigger detection → Retrain model → Version model → Promote to production

def test_model_versioning_rollback()
    # Register v1 → Promote v1 → Register v2 → Promote v2 → Rollback to v1

def test_ensemble_performance_adjustment()
    # Track individual models → Detect poor performer → Adjust weights → Verify improvement
```

### Performance Tests

```python
def test_performance_monitor_overhead()
    # Measure: Prediction tracking adds <10ms latency

def test_hyperparameter_search_time()
    # Measure: Grid search completes within expected time bounds

def test_database_query_performance()
    # Measure: Performance window queries <100ms

def test_concurrent_prediction_tracking()
    # Measure: Thread-safe tracking under concurrent predictions
```

### Validation Tests

```python
def test_config_validation()
    # Validate: All new config parameters have valid values

def test_database_schema_migrations()
    # Validate: New tables created successfully

def test_backward_compatibility()
    # Validate: Existing prediction code works unchanged
```

## Implementation Order

Phased implementation approach ensuring stability and testability at each step.

### Phase 1: Foundation & Monitoring (Days 1-3)

**Step 1.1: Type Definitions & Database Schema**

- Create src/bot_types/ml_types.py with all new types
- Add new tables to src/database/schema.py
- Run database migrations to create tables
- Verify schema with simple insert/select tests

**Step 1.2: ML Performance Repository**

- Create src/database/repositories/ml_performance_repository.py
- Implement all CRUD methods for new tables
- Integrate with DatabaseManager (add ml_performance property)
- Write unit tests for repository methods

**Step 1.3: Performance Monitor**

- Create src/ml/performance_monitor.py
- Implement prediction tracking and rolling metrics
- Implement degradation detection logic
- Write unit tests for all monitoring functions
- Create integration test with mock predictions

**Step 1.4: Update Configuration**

- Add ml.performance_monitoring section to config.yaml
- Add thresholds, window sizes, and alert settings
- Document all new configuration options

**Validation**: Performance monitoring working in isolation with test data

### Phase 2: Hyperparameter Tuning (Days 4-6)

**Step 2.1: Hyperparameter Tuner Core**

- Create src/ml/hyperparameter_tuner.py
- Implement grid search with scikit-learn GridSearchCV
- Implement random search with RandomizedSearchCV
- Add experiment tracking to database
- Write unit tests for search methods

**Step 2.2: Cross-Validation Integration**

- Add cross_validate() method to LSTMModelTrainer
- Implement k-fold CV for LSTM models
- Add CV results to experiment tracking
- Test with small dataset for speed

**Step 2.3: Model Optimizer**

- Create src/ml/model_optimizer.py
- Implement feature selection (SelectKBest, RFE)
- Implement architecture optimization for LSTM
- Test feature selection on existing feature set

**Step 2.4: Enhanced Model Training**

- Modify model_trainer.py to accept hyperparameter dicts
- Add save_experiment() method
- Integrate with MLPerformanceRepository
- Test training with experiment logging

**Validation**: Hyperparameter tuning produces measurable accuracy improvements

### Phase 3: Model Registry & Versioning (Days 7-8)

**Step 3.1: Model Registry**

- Create src/ml/model_registry.py
- Implement model registration and promotion
- Implement version comparison logic
- Write unit tests for registry operations

**Step 3.2: Version Management Integration**

- Modify model_trainer.py save_model() to use registry
- Modify predictor.py \_load_model() to load from registry
- Update ensemble.py to support versioned models
- Test version promotion workflow

**Step 3.3: Model Comparison Tools**

- Implement compare_models() method
- Add metrics visualization for comparison
- Create model history retrieval
- Test with multiple model versions

**Validation**: Models versioned correctly, can promote/rollback successfully

### Phase 4: Retraining Automation (Days 9-11)

**Step 4.1: Retraining Manager Core**

- Create src/ml/retraining_manager.py
- Implement trigger detection logic (accuracy_drop, time_based, data_drift)
- Implement execute_retraining() workflow
- Add rollback functionality
- Write unit tests for trigger detection

**Step 4.2: Integration with Performance Monitor**

- Connect RetrainingManager to PerformanceMonitor
- Implement automatic trigger checking
- Add retraining logging to database
- Test trigger detection with simulated degradation

**Step 4.3: Scheduled Retraining**

- Implement schedule_retraining() with APScheduler
- Add daily/weekly/monthly schedules
- Test scheduled execution
- Add manual trigger endpoint to dashboard

**Step 4.4: Trading Cycle Integration**

- Modify trading_cycle.py to include retraining checks
- Add retraining_manager to BotCoordinator
- Test full workflow: degradation → trigger → retrain → promote
- Verify bot continues operating during retraining

**Validation**: Retraining triggers correctly, executes successfully, promotes new model

### Phase 5: Predictor Integration (Days 12-13)

**Step 5.1: Performance Tracking in Predictions**

- Modify predictor.py predict_next_day() to track outcomes
- Add integration with PerformanceMonitor
- Test prediction tracking end-to-end
- Verify metrics calculated correctly

**Step 5.2: Ensemble Performance Tracking**

- Modify ensemble.py ensemble_predict() to log performance
- Implement dynamic_weight_adjustment()
- Test ensemble weight optimization
- Verify improved ensemble accuracy

**Step 5.3: Confidence Calibration Analysis**

- Implement get_confidence_calibration() in predictor
- Add calibration metrics to performance summary
- Test calibration calculation
- Create calibration visualization

**Validation**: Live predictions tracked accurately, ensemble weights adjusted based on performance

### Phase 6: Dashboard Integration (Days 14-15)

**Step 6.1: Performance API Endpoints**

- Add /api/ml/performance endpoint to app.py
- Add /api/ml/experiments endpoint
- Add /api/ml/models endpoint
- Add /api/ml/retrain endpoint
- Test all endpoints with Postman/curl

**Step 6.2: React Dashboard Components (Optional)**

- Create MLPerformancePage.tsx in React dashboard
- Add performance charts (accuracy over time, confidence calibration)
- Add experiment comparison table
- Add model version management UI
- Test dashboard integration

**Step 6.3: Configuration Updates**

- Add all ml.performance_monitoring config to config.yaml
- Add ml.hyperparameter_tuning config
- Add ml.retraining config
- Document all new configuration options
- Test configuration loading

**Validation**: Dashboard displays ML metrics, retraining can be triggered manually

### Phase 7: Testing & Validation (Days 16-18)

**Step 7.1: Comprehensive Unit Testing**

- Run all unit tests (8 test files)
- Achieve >80% code coverage
- Fix any failing tests
- Add edge case tests

**Step 7.2: Integration Testing**

- Run end-to-end integration tests
- Test with real historical data
- Verify all workflows (monitoring, tuning, retraining)
- Test rollback scenarios

**Step 7.3: Performance Testing**

- Measure performance monitoring overhead
- Measure database query performance
- Test concurrent prediction tracking
- Optimize any bottlenecks

**Step 7.4: Paper Trading Validation**

- Deploy to paper trading environment
- Monitor for 3-7 days
- Track real-world performance metrics
- Verify automatic retraining triggers correctly

**Validation**: All tests passing, system performing well in paper trading

### Phase 8: Documentation & Deployment (Days 19-20)

**Step 8.1: Code Documentation**

- Add docstrings to all new functions
- Add inline comments for complex logic
- Create API documentation for new endpoints
- Update README.md with new features

**Step 8.2: User Documentation**

- Create ML performance monitoring guide
- Create hyperparameter tuning guide
- Create retraining automation guide
- Document all new configuration options

**Step 8.3: Deployment Preparation**

- Update requirements.txt with new packages
- Create database migration script
- Test deployment on clean environment
- Create rollback procedures

**Step 8.4: Final Validation**

- Run full test suite
- Verify backward compatibility
- Check all endpoints working
- Validate configuration
- Final paper trading check

**Validation**: System fully documented, ready for production deployment

## Summary

This implementation plan provides a comprehensive system for measuring and improving ML accuracy through:

1. **Real-time Performance Monitoring** - Track every prediction, calculate rolling metrics, detect degradation automatically
2. **Systematic Hyperparameter Optimization** - Grid search, random search, Bayesian optimization with k-fold cross-validation
3. **Automated Model Retraining** - Trigger-based retraining with version management and rollback capability
4. **Production-Ready Infrastructure** - Database persistence, API endpoints, dashboard integration

**Total Estimated Timeline**: 18-20 days for full implementation

**Key Milestones**:

- Day 3: Performance monitoring operational
- Day 6: Hyperparameter tuning working
- Day 8: Model versioning complete
- Day 11: Automated retraining functional
- Day 13: Full prediction tracking integrated
- Day 15: Dashboard integration complete
- Day 18: Testing complete
- Day 20: Production deployment ready

**Success Metrics**:

- Model accuracy >60% directional prediction (current baseline)
- Degradation detected within 50 predictions
- Retraining improves accuracy by >5% points
- System overhead <10ms per prediction
- Zero prediction tracking failures
- Successful rollback to previous model when needed

**Next Steps After Implementation**:

1. Monitor performance for 2 weeks in paper trading
2. Analyze hyperparameter tuning results
3. Fine-tune retraining triggers based on real-world data
4. Consider adding advanced features (ensemble weight optimization, feature engineering automation)
5. Evaluate for live trading deployment
