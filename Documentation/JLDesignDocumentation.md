# Joblogic Design System Components

This documentation provides a comprehensive guide to all components in the Joblogic Design System, including their props, events, and usage examples.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Component Categories](#component-categories)
  - [Layout Components](#layout-components)
  - [Form Components](#form-components)
  - [Data Display Components](#data-display-components)
  - [Feedback Components](#feedback-components)
  - [Navigation Components](#navigation-components)
  - [Overlay Components](#overlay-components)
  - [Utility Components](#utility-components)
- [Component Documentation](#component-documentation)
  - [Button](#button)
  - [Input](#input)
  - [Select](#select)
  - [Checkbox](#checkbox)
  - [Radio](#radio)
  - [Modal](#modal)
  - [Dropdown](#dropdown)
  - [Table](#table)
  - [Tabs](#tabs)
  - [Card](#card)
  - [Alert](#alert)
  - [Toast](#toast)
  - [Tooltip](#tooltip)
  - [Badge](#badge)
  - [Avatar](#avatar)
  - [Icon](#icon)
  - [Spinner](#spinner)
  - [Pagination](#pagination)
  - [DatePicker](#datepicker)
  - [TimePicker](#timepicker)
  - [Progress](#progress)
- [Contributing](#contributing)

## Introduction

The Joblogic Design System provides a collection of reusable Vue components to build consistent user interfaces across Joblogic applications. This documentation serves as a reference for developers implementing these components.

## Getting Started

```vue
<template>
  <div>
    <j-button variant="primary">Click Me</j-button>
    <j-input placeholder="Enter text" />
    <j-select :options="[{ label: 'Option 1', value: '1' }]" />
  </div>
</template>

<script>
import { JButton, JInput, JSelect } from '@joblogic/design-system';

export default {
  components: {
    JButton,
    JInput,
    JSelect
  }
};
</script>
```

## Component Categories

### Layout Components
Components that help structure the page layout including grids, containers, and dividers.

### Form Components
Components used for user input such as text fields, selects, checkboxes, and radios.

### Data Display Components
Components that display data in various formats such as tables, lists, and cards.

### Feedback Components
Components that provide feedback to user actions including alerts, toasts, and progress indicators.

### Navigation Components
Components for navigation such as tabs, breadcrumbs, and pagination.

### Overlay Components
Components that overlay the UI such as modals, tooltips, and popovers.

### Utility Components
Utility components like icons, spinners, and dividers.

## Component Documentation

### Button

Buttons allow users to take actions, make choices, and navigate within a product or experience.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | 'primary' \| 'secondary' \| 'tertiary' \| 'danger' | 'primary' | The visual style of the button |
| size | 'small' \| 'medium' \| 'large' | 'medium' | The size of the button |
| disabled | boolean | false | Whether the button is disabled |
| fullWidth | boolean | false | Whether the button should take full width |
| type | 'button' \| 'submit' \| 'reset' | 'button' | The button type |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| click | MouseEvent | Emitted when the button is clicked |

#### Slots

| Name | Description |
|------|-------------|
| default | The content of the button |

#### Usage

```vue
<template>
  <!-- Primary button -->
  <j-button variant="primary">Submit</j-button>

  <!-- Secondary button -->
  <j-button variant="secondary">Cancel</j-button>

  <!-- Disabled button -->
  <j-button disabled>Disabled</j-button>

  <!-- Button with click handler -->
  <j-button @click="handleClick">Click Me</j-button>
</template>

<script>
import { JButton } from '@joblogic/design-system';

export default {
  components: {
    JButton
  },
  methods: {
    handleClick() {
      console.log('Button clicked');
    }
  }
};
</script>
```

### Input

Input components are used to get user input in a text field.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| modelValue | string | - | The controlled value of the input (v-model) |
| placeholder | string | - | Placeholder text |
| disabled | boolean | false | Whether the input is disabled |
| readonly | boolean | false | Whether the input is read-only |
| type | string | 'text' | The input type (text, password, email, etc.) |
| error | boolean \| string | false | Whether the input has an error or error message |
| size | 'small' \| 'medium' \| 'large' | 'medium' | The size of the input |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| update:modelValue | string | Emitted when the input value changes (for v-model) |
| focus | FocusEvent | Emitted when the input is focused |
| blur | FocusEvent | Emitted when the input loses focus |

#### Usage

```vue
<template>
  <!-- Basic input -->
  <j-input placeholder="Enter your name" />

  <!-- Password input -->
  <j-input type="password" placeholder="Enter password" />

  <!-- Controlled input with v-model -->
  <j-input 
    v-model="value" 
    placeholder="Controlled input" 
  />

  <!-- Input with error -->
  <j-input error="This field is required" />
</template>

<script>
import { ref } from 'vue';
import { JInput } from '@joblogic/design-system';

export default {
  components: {
    JInput
  },
  setup() {
    const value = ref('');
    return { value };
  }
};
</script>
```

### Select

Select components allow users to select from a list of options.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| modelValue | string \| number \| Array | - | The controlled value of the select (v-model) |
| options | Array<{ label: string, value: string \| number }> | [] | Options to display in the select |
| placeholder | string | 'Select...' | Placeholder text |
| disabled | boolean | false | Whether the select is disabled |
| multiple | boolean | false | Whether multiple options can be selected |
| error | boolean \| string | false | Whether the select has an error or error message |
| size | 'small' \| 'medium' \| 'large' | 'medium' | The size of the select |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| update:modelValue | string \| number \| Array | Emitted when the selection changes (for v-model) |
| focus | FocusEvent | Emitted when the select is focused |
| blur | FocusEvent | Emitted when the select loses focus |

#### Usage

```vue
<template>
  <!-- Basic select -->
  <j-select :options="options" placeholder="Choose an option" />

  <!-- Controlled select with v-model -->
  <j-select 
    v-model="selected"
    :options="options"
  />

  <!-- Multi-select -->
  <j-select :options="options" multiple />
</template>

<script>
import { ref } from 'vue';
import { JSelect } from '@joblogic/design-system';

export default {
  components: {
    JSelect
  },
  setup() {
    const selected = ref('');
    const options = [
      { label: 'Option 1', value: '1' },
      { label: 'Option 2', value: '2' },
      { label: 'Option 3', value: '3' },
    ];
    
    return { selected, options };
  }
};
</script>
```

### Table

Tables display data in rows and columns.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| data | Array<Object> | [] | Array of data objects to display |
| columns | Array<{ header: string, field: string, formatter?: Function }> | [] | Column configuration |
| striped | boolean | false | Whether to use striped rows |
| bordered | boolean | false | Whether to show borders around cells |
| hoverable | boolean | false | Whether rows should change style on hover |
| sortable | boolean | false | Whether columns are sortable |
| pagination | boolean \| Object | false | Whether to enable pagination |
| loading | boolean | false | Whether the table is in loading state |
| emptyMessage | string | 'No data available' | Message to show when there's no data |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| row-click | { row: Object, index: number } | Emitted when a row is clicked |
| sort | { field: string, direction: 'asc' \| 'desc' } | Emitted when a sortable column is clicked |

#### Slots

| Name | Props | Description |
|------|-------|-------------|
| empty | - | Custom empty state content |
| [column.field] | { row, value } | Custom cell content for the specified column |

#### Usage

```vue
<template>
  <j-table 
    :data="data" 
    :columns="columns"
    striped
    hoverable 
    @row-click="handleRowClick"
  >
    <template #actions="{ row }">
      <j-button @click="handleAction(row.id)">Edit</j-button>
    </template>
  </j-table>
</template>

<script>
import { JTable, JButton } from '@joblogic/design-system';

export default {
  components: {
    JTable,
    JButton
  },
  data() {
    return {
      data: [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
      ],
      columns: [
        { header: 'ID', field: 'id' },
        { header: 'Name', field: 'name' },
        { header: 'Email', field: 'email' },
        { header: 'Actions', field: 'actions' }
      ]
    };
  },
  methods: {
    handleRowClick(row) {
      console.log('Row clicked:', row);
    },
    handleAction(id) {
      console.log('Action for ID:', id);
    }
  }
};
</script>
```

### Modal

Modals display content that requires user interaction in a layer above the page.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| modelValue | boolean | false | Whether the modal is visible (v-model) |
| title | string | - | Modal title |
| size | 'small' \| 'medium' \| 'large' \| 'full' | 'medium' | The size of the modal |
| closeOnEsc | boolean | true | Whether the modal can be closed by pressing Escape |
| closeOnOverlayClick | boolean | true | Whether clicking the overlay closes the modal |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| update:modelValue | boolean | Emitted when the modal visibility changes (for v-model) |
| close | - | Emitted when the modal is closed |

#### Slots

| Name | Description |
|------|-------------|
| default | Modal content |
| title | Custom title content |
| footer | Modal footer content |

#### Usage

```vue
<template>
  <div>
    <j-button @click="isOpen = true">Open Modal</j-button>
    
    <j-modal
      v-model="isOpen"
      title="Example Modal"
    >
      <p>This is the modal content.</p>
      
      <template #footer>
        <j-button @click="isOpen = false">Close</j-button>
      </template>
    </j-modal>
  </div>
</template>

<script>
import { ref } from 'vue';
import { JModal, JButton } from '@joblogic/design-system';

export default {
  components: {
    JModal,
    JButton
  },
  setup() {
    const isOpen = ref(false);
    return { isOpen };
  }
};
</script>
```

## Contributing

Guidelines for contributing to the component library:

1. Follow the Vue style guide and coding standards
2. Write tests for new components
3. Document props, events, slots, and usage examples
4. Submit a pull request for review

For more information, see the [Contribution Guidelines](CONTRIBUTING.md).
