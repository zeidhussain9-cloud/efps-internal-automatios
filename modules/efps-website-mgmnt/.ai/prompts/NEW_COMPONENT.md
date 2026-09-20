# Prompt Template: Create New Component

Use this template when you need an AI agent to create a new UI component.

---

**Task**: Create a new component named `[COMPONENT_NAME]`.

**Requirements**:
- **Location**: `src/components/[COMPONENT_NAME].tsx`
- **Styling**: Use Tailwind CSS 4 utility classes.
- **Typing**: Use TypeScript for props and state.
- **Accessibility**: Ensure proper semantic HTML and ARIA labels.

**Context**:
- This component will be used in `[PARENT_COMPONENT]`.
- It should follow the design system defined in `src/styles.css`.

**Example Usage**:
```tsx
import [COMPONENT_NAME] from "@/components/[COMPONENT_NAME]";

function Parent() {
  return <[COMPONENT_NAME] />;
}
```
