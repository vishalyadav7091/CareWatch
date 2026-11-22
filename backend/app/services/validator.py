class VitalValidator:
    """Validates physiological readings against biological boundaries and clinical realism."""

    # Plausible biological boundaries for ICU monitoring
    PHYSIOLOGICAL_LIMITS = {
        "heart_rate": (20.0, 300.0),        # bpm
        "spo2": (50.0, 100.0),              # %
        "systolic_bp": (40.0, 300.0),       # mmHg
        "diastolic_bp": (20.0, 200.0),      # mmHg
        "respiratory_rate": (4.0, 80.0),    # breaths/min
        "temperature": (28.0, 44.0),        # Celsius
    }

    @classmethod
    def validate(cls, reading):
        """Validate an observation dictionary.
        
        Returns (is_valid, quality_status, error_messages)
        """
        errors = []
        status = "valid"

        for param, (min_val, max_val) in cls.PHYSIOLOGICAL_LIMITS.items():
            val = reading.get(param)
            if val is not None:
                try:
                    num_val = float(val)
                    if num_val < min_val or num_val > max_val:
                        errors.append(
                            f"{param} value {num_val} is out of biological bounds ({min_val}-{max_val})"
                        )
                        status = "invalid"
                except (ValueError, TypeError):
                    errors.append(f"{param} must be numeric")
                    status = "invalid"

        # Check blood pressure logic (systolic must be greater than diastolic)
        sbp = reading.get("systolic_bp")
        dbp = reading.get("diastolic_bp")
        if sbp is not None and dbp is not None:
            try:
                if float(sbp) <= float(dbp):
                    errors.append("Systolic BP must be strictly greater than Diastolic BP")
                    status = "invalid"
            except (ValueError, TypeError):
                pass

        is_valid = len(errors) == 0
        return is_valid, status, errors

