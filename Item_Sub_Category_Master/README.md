# Item Sub Category Master

This customization automatically generates the subcategory code when a new item subcategory is created.

## Features
1. **Auto-generated Code**: When inserting a new subcategory, if `subcategory_code` is empty, it finds the next sequence for the given category parent and letter prefix (e.g. `D001` → `D002`).

## Setup Instructions

### 1. DocType Setup
Create a new DocType `Item Sub Category Master` (or customize it) with the following fields:
- `parent_category` (Link to parent Category)
- `letter_prefix` (Data/Select, e.g. `D`)
- `subcategory_code` (Data, read-only)

### 2. Server Script
- **DocType**: `Item Sub Category Master`
- **Script Type**: `Document Event`
- **DocType Event**: `Before Insert` (or `Before Save` / custom script hook)
- **Script**: Paste the contents of `Server_Script.py`
