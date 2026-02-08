# Data Loading Infrastructure Review

## Current Capabilities

### ✅ Supported Data Sources

1. **Mock Data** (`MockDataLoader`)
   - Deterministic generation with configurable parameters
   - Seed-based for reproducibility
   - Configurable size, anomaly count, and multiplier

2. **CSV Files** (`CSVDataLoader`)
   - Loads from CSV files
   - Configurable column names (value, timestamp, anomaly)
   - Handles missing anomaly column (defaults to False)

3. **JSON Files** (`JSONDataLoader`)
   - Supports array of objects format
   - Supports object with arrays format
   - Configurable key names

4. **Time-Series Data** (`TimeSeriesDataLoader`)
   - Wrapper around CSV/JSON loaders
   - Auto-detects format from file extension

### ✅ Integration Points

1. **Config-Based Loading**
   - `create_data_loader(config)` factory function
   - Automatically creates appropriate loader from `DataConfig`
   - Used by `evolve()` function

2. **Direct Injection** (NEW)
   - `evolve()` now accepts optional `data_loader` parameter
   - Allows programmatic injection of custom DataLoaders
   - Overrides config-based loading when provided

3. **Fitness Function Integration**
   - `fitness()` accepts optional `data_loader` parameter
   - Falls back to mock data if not provided

### ✅ Custom DataLoader Support

Users can create custom DataLoaders by:
1. Subclassing `DataLoader` ABC
2. Implementing `load() -> Tuple[List[float], List[bool]]`
3. Injecting via `evolve(data_loader=my_loader)`

See `examples/custom_data_loader.py` for examples.

## Data Format Requirements

### Input Format
- **Values**: List of floats (numeric time-series data)
- **Anomalies**: List of booleans (same length as values)
  - `True` = anomaly detected
  - `False` = normal data point

### CSV Format
```csv
value,timestamp,is_anomaly
45.2,2024-01-01T00:00:00,False
125.8,2024-01-01T00:03:00,True
```

### JSON Format (Array of Objects)
```json
[
  {"value": 45.2, "timestamp": "2024-01-01T00:00:00", "is_anomaly": false},
  {"value": 125.8, "timestamp": "2024-01-01T00:03:00", "is_anomaly": true}
]
```

### JSON Format (Object with Arrays)
```json
{
  "value": [45.2, 125.8, 49.5],
  "timestamp": ["2024-01-01T00:00:00", "2024-01-01T00:03:00", "2024-01-01T00:04:00"],
  "is_anomaly": [false, true, false]
}
```

## Usage Examples

### Via Config File
```yaml
data:
  data_source: csv
  data_path: data/my_data.csv
  value_column: latency
  anomaly_column: is_anomaly
```

### Via CLI
```bash
python -m alert_axolotl_evo.main --data-source csv --data-path data.csv --value-column latency
```

### Programmatic Injection
```python
from alert_axolotl_evo.data import DataLoader
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config

class MyDataLoader(DataLoader):
    def load(self):
        # Fetch from API, database, etc.
        values = [45.2, 48.1, 125.8]
        anomalies = [False, False, True]
        return values, anomalies

config = Config()
my_loader = MyDataLoader()
evolve(config=config, data_loader=my_loader)
```

## Current Limitations & Considerations

### ⚠️ Limitations

1. **Single Data Source Per Run**
   - Each evolution run uses one DataLoader
   - No built-in support for data rotation or multi-source blending

2. **Data Caching**
   - CSV/JSON loaders read from disk on every `load()` call
   - No built-in caching (may be slow for large files)

3. **Anomaly Label Handling**
   - If `anomaly_column` is not provided, all points default to `False`
   - No automatic anomaly detection (requires labeled data)

4. **Data Validation**
   - Minimal validation of data format
   - Errors are caught but may not be descriptive

### ✅ Strengths

1. **Clean Abstraction**
   - `DataLoader` ABC provides clear interface
   - Easy to extend with custom implementations

2. **Flexible Integration**
   - Works with config files, CLI, and programmatic injection
   - `fitness()` function accepts optional loader

3. **Error Handling**
   - Graceful fallback to mock data if loading fails
   - Continues evolution even if data source has issues

## Recommendations

### For External Data Injection

1. **Use Custom DataLoader for API/Database Sources**
   ```python
   class APIDataLoader(DataLoader):
       def load(self):
           # Fetch from your API
           response = requests.get(self.api_url)
           data = response.json()
           return self._parse_data(data)
   ```

2. **Use In-Memory Loader for Programmatic Data**
   ```python
   # No need to write to file
   loader = InMemoryDataLoader(values, anomalies)
   evolve(config=config, data_loader=loader)
   ```

3. **Use CSV/JSON for File-Based Data**
   - Standard formats work out of the box
   - Configure via config file or CLI

### Testing External Data

1. **Verify Data Format**
   - Ensure values are numeric (float-compatible)
   - Ensure anomalies are boolean or boolean-like
   - Ensure equal lengths

2. **Test DataLoader Separately**
   ```python
   loader = MyDataLoader()
   values, anomalies = loader.load()
   assert len(values) == len(anomalies)
   assert all(isinstance(v, (int, float)) for v in values)
   assert all(isinstance(a, bool) for a in anomalies)
   ```

3. **Use Small Test Runs**
   - Start with small pop_size and generations
   - Verify fitness evaluation works with your data

## Summary

✅ **External data injection is fully supported** via:
- CSV/JSON file loaders (config-based)
- Custom DataLoader subclassing (programmatic)
- Direct injection into `evolve()` function

The infrastructure is clean, extensible, and ready for real-world data sources.
