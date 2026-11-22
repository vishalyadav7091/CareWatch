from datetime import datetime, timezone


class VitalNormalizer:
    """Normalizes timestamps, numeric precisions, and units."""

    @staticmethod
    def normalize_timestamp(timestamp_val):
        """Converts diverse timestamp representations into standard UTC datetime object."""
        if isinstance(timestamp_val, datetime):
            if timestamp_val.tzinfo is None:
                return timestamp_val.replace(tzinfo=timezone.utc)
            return timestamp_val.astimezone(timezone.utc)

        if isinstance(timestamp_val, str):
            try:
                # Handle ISO8601 with trailing Z or timezone offsets
                clean_str = timestamp_val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                pass

        # Fallback to current UTC time
        return datetime.now(timezone.utc)

    @classmethod
    def normalize_reading(cls, raw_reading):
        """Clean and normalize a physiological reading dictionary."""
        def _to_float(v, decimal_places=2):
            if v is None:
                return None
            try:
                return round(float(v), decimal_places)
            except (ValueError, TypeError):
                return None

        # Convert Fahrenheit to Celsius if flagged
        temp = _to_float(raw_reading.get("temperature"))
        is_fahrenheit = (raw_reading.get("temp_unit") == "F" or raw_reading.get("temperature_unit") == "F")
        if is_fahrenheit and temp is not None:
            temp = round((temp - 32.0) * (5.0 / 9.0), 2)

        return {
            "patient_id": raw_reading.get("patient_id"),
            "device_id": raw_reading.get("device_id"),
            "heart_rate": _to_float(raw_reading.get("heart_rate")),
            "spo2": _to_float(raw_reading.get("spo2")),
            "systolic_bp": _to_float(raw_reading.get("systolic_bp")),
            "diastolic_bp": _to_float(raw_reading.get("diastolic_bp")),
            "respiratory_rate": _to_float(raw_reading.get("respiratory_rate")),
            "temperature": temp,
            "measurement_source": raw_reading.get("measurement_source", "simulator"),
            "data_quality": raw_reading.get("data_quality", "valid"),
            "measured_at": cls.normalize_timestamp(raw_reading.get("measured_at")),
        }

