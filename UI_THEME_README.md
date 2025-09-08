# 🎨 FWMIS Professional UI Theme System

## Overview

The FWMIS Professional UI Theme System provides a centralized, consistent styling framework for the entire application. This ensures a cohesive, modern, and professional user experience across all dialogs and components.

## 🚀 Quick Start

### 1. Import the Theme Module

```python
from scripts.Utilities.ui_theme import (
    apply_theme, create_professional_button, create_professional_groupbox,
    setup_professional_table, create_status_label, get_button_style,
    get_groupbox_style, COLORS
)
```

### 2. Apply Theme to Dialog

```python
class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_theme(self)  # Apply professional theme
        self.setWindowTitle("🎯 My Professional Dialog")
        self.setFixedSize(800, 600)
        self.setup_ui()
```

### 3. Use Professional Components

```python
# Instead of plain buttons
button = create_professional_button("💾 Save", "success", "normal")

# Instead of plain group boxes
group = create_professional_groupbox("📋 Data Section", "blue")

# Instead of plain tables
setup_professional_table(table, headers=["Name", "Value"], emojis=["👤", "💰"])

# Instead of plain status messages
status = create_status_label("Operation completed", "success")
```

## 🎨 Design System

### Color Palette

| Color | Hex Code | Usage |
|-------|----------|-------|
| **Primary** | `#007bff` | Primary actions, links, focus states |
| **Success** | `#28a745` | Success states, confirmations |
| **Warning** | `#fd7e14` | Warnings, secondary actions |
| **Danger** | `#dc3545` | Errors, critical actions |
| **Info** | `#17a2b8` | Information, help actions |
| **Secondary** | `#6c757d` | Cancel, secondary actions |
| **Light** | `#f8f9fa` | Backgrounds |
| **Dark** | `#343a40` | Primary text |

### Typography

- **Primary Font**: System font stack (cross-platform compatible)
- **Headers**: 18px, bold, dark color
- **Labels**: 13px, 500 weight, dark color
- **Body Text**: 13px, 400 weight, dark color
- **Small Text**: 12px, 400 weight, muted color

### Spacing & Layout

- **Dialog Margins**: 20px
- **Section Spacing**: 15px
- **Element Spacing**: 10-12px
- **Button Height**: 35px (normal), 45px (large)
- **Input Height**: 35px minimum
- **Table Row Height**: 60px minimum

## 📚 Component Library

### Buttons

```python
# Primary action button
save_btn = create_professional_button("💾 Save", "primary", "normal")

# Success button
confirm_btn = create_professional_button("✅ Confirm", "success", "large")

# Warning button
warning_btn = create_professional_button("⚠️ Proceed", "warning", "normal")

# Danger button
delete_btn = create_professional_button("🗑️ Delete", "danger", "normal")

# Info button
help_btn = create_professional_button("❓ Help", "info", "small")

# Secondary button
cancel_btn = create_professional_button("❌ Cancel", "secondary", "normal")
```

### Group Boxes

```python
# Blue theme (default/primary sections)
file_group = create_professional_groupbox("📁 File Selection", "blue")

# Green theme (success/data sections)
data_group = create_professional_groupbox("📊 Data Analysis", "green")

# Purple theme (management sections)
admin_group = create_professional_groupbox("👥 User Management", "purple")

# Red theme (critical sections)
error_group = create_professional_groupbox("🚨 Critical Actions", "red")
```

### Tables

```python
# Setup professional table
table = QTableWidget()
setup_professional_table(
    table,
    headers=["🏷️ ID", "📝 Name", "💰 Amount", "📅 Date"],
    emojis=["🏷️", "📝", "💰", "📅"]
)

# Set column widths
table.setColumnWidth(0, 80)
table.setColumnWidth(1, 150)
table.setColumnWidth(2, 100)
table.setColumnWidth(3, 120)
```

### Status Messages

```python
# Success status
status = create_status_label("✅ Operation completed successfully!", "success")

# Warning status
status = create_status_label("⚠️ Please review before proceeding", "warning")

# Error status
status = create_status_label("❌ Operation failed", "error")

# Info status
status = create_status_label("ℹ️ Processing data...", "info")
```

## 🎯 Icon Conventions

| Icon | Usage | Example |
|------|-------|---------|
| 📊 | Data/Analytics | Tables, reports, statistics |
| 📁 | Files/Folders | File selection, directories |
| ⚙️ | Settings/Config | Configuration, preferences |
| 🎯 | Actions/Targets | Primary actions, goals |
| ✅ | Success/Valid | Confirmations, valid states |
| ❌ | Cancel/Error | Cancel actions, errors |
| 🔍 | Search/Find | Search functions, filters |
| 💾 | Save | Save operations |
| 👥 | People/Users | User management, profiles |
| 📋 | Lists/Tasks | Task lists, checklists |
| 💰 | Money/Finance | Financial data, amounts |
| 📅 | Dates/Calendar | Date selection, scheduling |
| 🏢 | Organizations | Company/department selection |
| 🔢 | Numbers/IDs | IDs, reference numbers |

## 🔧 Implementation Guide

### Converting Existing Dialogs

1. **Add Theme Import**
```python
from scripts.Utilities.ui_theme import (
    apply_theme, create_professional_button, create_professional_groupbox,
    setup_professional_table, create_status_label
)
```

2. **Apply Theme in Constructor**
```python
def __init__(self, parent=None):
    super().__init__(parent)
    apply_theme(self)  # Apply professional theme
    self.setWindowTitle("🎯 Dialog Title")
    self.setFixedSize(width, height)
```

3. **Replace Inline Styles**
```python
# Before
button = QPushButton("Save")
button.setStyleSheet("QPushButton { background-color: #007bff; color: white; }")

# After
button = create_professional_button("💾 Save", "primary", "normal")
```

4. **Update Group Boxes**
```python
# Before
group = QGroupBox("Section")
group.setStyleSheet("QGroupBox { border: 2px solid #dee2e6; }")

# After
group = create_professional_groupbox("📋 Section", "blue")
```

5. **Update Tables**
```python
# Before
table = QTableWidget()
table.setStyleSheet("QTableWidget { border: 1px solid #ced4da; }")

# After
table = QTableWidget()
setup_professional_table(table, headers=["Col1", "Col2"], emojis=["📝", "💰"])
```

### Best Practices

1. **Consistent Naming**: Use descriptive names with emojis
2. **Proper Sizing**: Follow the spacing and sizing guidelines
3. **Color Coding**: Use colors consistently for similar actions
4. **Accessibility**: Ensure sufficient contrast and readable text
5. **Testing**: Test on different screen sizes and resolutions

### Responsive Design

- Use minimum widths/heights appropriately
- Test on different screen sizes
- Ensure text doesn't get cut off
- Consider high-DPI displays

## 📋 Migration Checklist

- [ ] Import theme module in dialog
- [ ] Apply `apply_theme()` in constructor
- [ ] Replace all `QPushButton` with `create_professional_button()`
- [ ] Replace all `QGroupBox` with `create_professional_groupbox()`
- [ ] Update all tables with `setup_professional_table()`
- [ ] Replace status messages with `create_status_label()`
- [ ] Remove all inline stylesheets
- [ ] Test dialog functionality
- [ ] Test on different screen sizes
- [ ] Verify accessibility compliance

## 🎨 Advanced Customization

### Custom Button Styles

```python
# Custom button style
custom_style = get_button_style("primary", "large") + """
    QPushButton {
        font-weight: bold;
        text-transform: uppercase;
    }
"""

button = QPushButton("Custom Button")
button.setStyleSheet(custom_style)
```

### Custom Group Box Styles

```python
# Custom group box style
custom_group_style = get_groupbox_style("blue") + """
    QGroupBox {
        background-color: #f0f8ff;
    }
"""

group = QGroupBox("Custom Group")
group.setStyleSheet(custom_group_style)
```

### Extending the Theme

To add new components to the theme system:

1. Add the component function to `ui_theme.py`
2. Follow the existing naming conventions
3. Include proper documentation
4. Test across different use cases

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all PyQt5 components are imported
2. **Styling Not Applied**: Check that `apply_theme()` is called
3. **Text Cut Off**: Increase minimum heights for buttons/tables
4. **Color Issues**: Verify color contrast ratios
5. **Layout Problems**: Check spacing and margin values

### Debug Tips

- Use browser developer tools equivalent for Qt (Qt Designer)
- Check console for styling errors
- Test on different operating systems
- Verify font availability

## 📞 Support

For questions about the UI theme system:

1. Check this documentation first
2. Review the example implementation in `ui_theme_example.py`
3. Look at the Import Undisclosed Cases dialog as a reference
4. Contact the development team for assistance

---

**Remember**: Consistency is key to a professional user experience. Always use the theme system for new features and gradually migrate existing dialogs to maintain a cohesive application appearance! 🚀