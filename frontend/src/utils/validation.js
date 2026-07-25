/**
 * Centralized validation rules for the entire application.
 * Each rule returns an error string or empty string on success.
 */

const isPresent = (val) => val !== undefined && val !== null && String(val).trim() !== "";

// ─── Phone ─────────────────────────────────────────────────────

export const PHONE_RULES = {
  placeholder: "Enter 10-digit phone number",
  helper: "Phone number must contain exactly 10 digits.",
};

export function validatePhone(val, required = false) {
  if (required && !isPresent(val)) return "Phone number is required.";
  if (!isPresent(val)) return "";
  const cleaned = String(val).replace(/\s/g, "");
  if (!/^\d+$/.test(cleaned)) return "Phone number can contain digits only.";
  if (cleaned.length !== 10) return "Enter a valid 10-digit phone number.";
  return "";
}

// ─── Email ─────────────────────────────────────────────────────

export const EMAIL_RULES = {
  placeholder: "Enter email address",
  helper: "Example: user@example.com",
};

export function validateEmail(val, required = false) {
  if (required && !isPresent(val)) return "Email address is required.";
  if (!isPresent(val)) return "";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(val).trim())) return "Enter a valid email address.";
  return "";
}

// ─── Aadhaar ───────────────────────────────────────────────────

export const AADHAAR_RULES = {
  placeholder: "Enter 12-digit Aadhaar number",
  helper: "Aadhaar number must contain exactly 12 digits.",
};

export function validateAadhaar(val, required = false) {
  if (required && !isPresent(val)) return "Aadhaar number is required.";
  if (!isPresent(val)) return "";
  if (!/^\d{12}$/.test(String(val).trim())) return "Enter a valid 12-digit Aadhaar number.";
  return "";
}

// ─── PAN ────────────────────────────────────────────────────────

export const PAN_RULES = {
  placeholder: "Enter PAN number",
  helper: "Format: ABCDE1234F",
};

export function validatePAN(val, required = false) {
  if (required && !isPresent(val)) return "PAN number is required.";
  if (!isPresent(val)) return "";
  if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(String(val).toUpperCase().trim())) return "Enter a valid PAN number.";
  return "";
}

// ─── Bank Account ──────────────────────────────────────────────

export const ACCOUNT_RULES = {
  placeholder: "Enter account number",
  helper: "Enter a valid bank account number.",
};

export function validateAccount(val, required = false) {
  if (required && !isPresent(val)) return "Account number is required.";
  if (!isPresent(val)) return "";
  if (!/^\d+$/.test(String(val).trim())) return "Account number must contain only numbers.";
  const len = String(val).trim().length;
  if (len < 9 || len > 18) return "Account number must be between 9 and 18 digits.";
  return "";
}

// ─── IFSC ──────────────────────────────────────────────────────

export const IFSC_RULES = {
  placeholder: "Enter IFSC code",
  helper: "Format: SBIN0001234",
};

export function validateIFSC(val, required = false) {
  if (required && !isPresent(val)) return "IFSC code is required.";
  if (!isPresent(val)) return "";
  if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(String(val).toUpperCase().trim())) return "Enter a valid IFSC code.";
  return "";
}

// ─── Amount ────────────────────────────────────────────────────

export const AMOUNT_RULES = {
  placeholder: "Enter amount",
};

export function validateAmount(val, required = false) {
  if (required && !isPresent(val)) return "Amount is required.";
  if (!isPresent(val)) return "";
  if (isNaN(Number(val))) return "Amount cannot contain letters.";
  if (Number(val) <= 0) return "Amount must be greater than zero.";
  return "";
}

// ─── Age ────────────────────────────────────────────────────────

export const AGE_RULES = {
  placeholder: "Enter age",
};

export function validateAge(val, required = false) {
  if (required && !isPresent(val)) return "Age is required.";
  if (!isPresent(val)) return "";
  if (!/^\d+$/.test(String(val).trim())) return "Only numbers are allowed.";
  const age = parseInt(val, 10);
  if (age < 0 || age > 120) return "Age must be between 0 and 120.";
  return "";
}

// ─── Name ──────────────────────────────────────────────────────

export const NAME_RULES = {
  placeholder: "Enter full name",
};

export function validateName(val, required = false) {
  if (required && !isPresent(val)) return "Name is required.";
  if (!isPresent(val)) return "";
  const trimmed = String(val).trim();
  if (/\d/.test(trimmed)) return "Name cannot contain numbers.";
  if (trimmed.length < 2) return "Name must be between 2 and 100 characters.";
  if (trimmed.length > 100) return "Name must be between 2 and 100 characters.";
  return "";
}

// ─── FIR Number ────────────────────────────────────────────────

export const FIR_NUMBER_RULES = {
  placeholder: "Enter FIR number",
};

export function validateFIRNumber(val, required = false) {
  if (required && !isPresent(val)) return "FIR number is required.";
  if (!isPresent(val)) return "";
  if (String(val).trim().length < 2) return "Enter a valid FIR number.";
  return "";
}

// ─── Password ──────────────────────────────────────────────────

export const PASSWORD_RULES = {
  placeholder: "Enter password",
  helper: "Password must contain at least 8 characters including uppercase, lowercase, number and special character.",
};

export function validatePassword(val, required = false) {
  if (required && !isPresent(val)) return "Password is required.";
  if (!isPresent(val)) return "";
  const v = String(val);
  if (v.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Z]/.test(v)) return "Password must contain one uppercase letter.";
  if (!/[a-z]/.test(v)) return "Password must contain one lowercase letter.";
  if (!/\d/.test(v)) return "Password must contain one number.";
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(v)) return "Password must contain one special character.";
  return "";
}

// ─── Confirm Password ──────────────────────────────────────────

export function validateConfirmPassword(val, passwordVal, required = false) {
  if (required && !isPresent(val)) return "Confirm password is required.";
  if (!isPresent(val)) return "";
  if (val !== passwordVal) return "Passwords do not match.";
  return "";
}

// ─── Username ──────────────────────────────────────────────────

export const USERNAME_RULES = {
  placeholder: "Enter username",
};

export function validateUsername(val, required = false) {
  if (required && !isPresent(val)) return "Username is required.";
  if (!isPresent(val)) return "";
  const v = String(val).trim();
  if (v.length < 4 || v.length > 30) return "Username must be between 4 and 30 characters.";
  if (!/^[a-zA-Z0-9_]+$/.test(v)) return "Only letters, numbers and underscore (_) are allowed.";
  return "";
}

// ─── Address ───────────────────────────────────────────────────

export const ADDRESS_RULES = {
  placeholder: "Enter address",
};

export function validateAddress(val, required = false) {
  if (required && !isPresent(val)) return "Address is required.";
  if (!isPresent(val)) return "";
  if (String(val).trim().length > 255) return "Address cannot exceed 255 characters.";
  return "";
}

// ─── Date (no future dates by default) ─────────────────────────

export function validateDate(val, required = false, allowFuture = false) {
  if (required && !isPresent(val)) return "Please select a valid date.";
  if (!isPresent(val)) return "";
  const d = new Date(val);
  if (isNaN(d.getTime())) return "Please select a valid date.";
  if (!allowFuture && d > new Date()) return "Future dates are not allowed.";
  return "";
}

// ─── Time ──────────────────────────────────────────────────────

export function validateTime(val, required = false) {
  if (required && !isPresent(val)) return "Please select a valid time.";
  if (!isPresent(val)) return "";
  if (!/^\d{2}:\d{2}(:\d{2})?$/.test(String(val).trim())) return "Please select a valid time.";
  return "";
}

// ─── Latitude ──────────────────────────────────────────────────

export const LATITUDE_RULES = {
  placeholder: "Enter latitude",
};

export function validateLatitude(val, required = false) {
  if (required && !isPresent(val)) return "Latitude is required.";
  if (!isPresent(val)) return "";
  const num = Number(val);
  if (isNaN(num)) return "Latitude must be between -90 and 90.";
  if (num < -90 || num > 90) return "Latitude must be between -90 and 90.";
  return "";
}

// ─── Longitude ─────────────────────────────────────────────────

export const LONGITUDE_RULES = {
  placeholder: "Enter longitude",
};

export function validateLongitude(val, required = false) {
  if (required && !isPresent(val)) return "Longitude is required.";
  if (!isPresent(val)) return "";
  const num = Number(val);
  if (isNaN(num)) return "Longitude must be between -180 and 180.";
  if (num < -180 || num > 180) return "Longitude must be between -180 and 180.";
  return "";
}

// ─── Vehicle Number ────────────────────────────────────────────

export const VEHICLE_RULES = {
  placeholder: "Enter vehicle number",
  helper: "Example: TN10AB1234",
};

export function validateVehicle(val, required = false) {
  if (required && !isPresent(val)) return "Vehicle number is required.";
  if (!isPresent(val)) return "";
  if (!/^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{1,4}$/i.test(String(val).trim())) return "Enter a valid vehicle registration number.";
  return "";
}

// ─── Required Dropdown ─────────────────────────────────────────

export function validateDropdown(val, required = false) {
  if (required && (!isPresent(val) || val === "")) return "Please select an option.";
  return "";
}

// ─── Remarks / Description ─────────────────────────────────────

export function validateRemarks(val, required = false) {
  if (required && !isPresent(val)) return "This field is required.";
  if (!isPresent(val)) return "";
  if (String(val).length > 1000) return "Remarks cannot exceed 1000 characters.";
  return "";
}

// ─── Numeric ID ────────────────────────────────────────────────

export function validateNumericId(val, required = false) {
  if (required && !isPresent(val)) return "This field is required.";
  if (!isPresent(val)) return "";
  if (!/^\d+$/.test(String(val).trim())) return "Only numeric values are allowed.";
  return "";
}

// ─── Required Field (generic) ──────────────────────────────────

export function validateRequired(val, fieldName = "This field") {
  if (!isPresent(val)) return fieldName + " is required.";
  return "";
}

// ─── Search placeholder ────────────────────────────────────────

export const SEARCH_RULES = {
  placeholder: "Search...",
};

// ─── Bundle: validate all fields in a form object ──────────────

export function validateForm(form, rules) {
  const errors = {};
  for (const [field, [fn, required]] of Object.entries(rules)) {
    const err = fn(form[field], required);
    if (err) errors[field] = err;
  }
  return errors;
}
