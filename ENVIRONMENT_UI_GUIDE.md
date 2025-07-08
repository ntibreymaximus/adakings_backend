# Environment UI Tags Integration Guide

This guide explains how to integrate environment UI tags in your frontend application.

## API Endpoint

**GET** `/api/environment/`

Returns environment information for UI display purposes.

## Response Format

```json
{
  "environment": "development",
  "platform": "Railway", 
  "debug": true,
  "version": "1.0.0",
  "ui_tag": "dev-server",
  "show_tag": true
}
```

## Field Descriptions

- **environment**: Current environment (`local`, `development`, `production`)
- **platform**: Platform (`Railway`, `Local`)
- **debug**: Debug mode status
- **version**: Application version
- **ui_tag**: Tag to display in UI (`local`, `dev-server`, `null`)
- **show_tag**: Whether to show the environment tag

## UI Tag Display Logic

| Environment | Platform | UI Tag | Show Tag | Description |
|-------------|----------|---------|----------|-------------|
| local | Local | `local` | `true` | Local development |
| development | Railway | `dev-server` | `true` | Development server |
| production | Railway | `null` | `false` | Production (no tag) |

## Frontend Implementation Examples

### React Example

```jsx
import React, { useState, useEffect } from 'react';

const EnvironmentTag = () => {
  const [envInfo, setEnvInfo] = useState(null);

  useEffect(() => {
    fetch('/api/environment/')
      .then(response => response.json())
      .then(data => setEnvInfo(data));
  }, []);

  if (!envInfo || !envInfo.show_tag) {
    return null;
  }

  const getTagStyle = (tag) => {
    switch (tag) {
      case 'local':
        return {
          backgroundColor: '#4CAF50',
          color: 'white',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 'bold'
        };
      case 'dev-server':
        return {
          backgroundColor: '#FF9800',
          color: 'white',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 'bold'
        };
      default:
        return {};
    }
  };

  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      zIndex: 9999 
    }}>
      <span style={getTagStyle(envInfo.ui_tag)}>
        {envInfo.ui_tag.toUpperCase()}
      </span>
    </div>
  );
};

export default EnvironmentTag;
```

### Vue.js Example

```vue
<template>
  <div v-if="envInfo && envInfo.show_tag" class="environment-tag" :class="tagClass">
    {{ envInfo.ui_tag.toUpperCase() }}
  </div>
</template>

<script>
export default {
  name: 'EnvironmentTag',
  data() {
    return {
      envInfo: null
    };
  },
  computed: {
    tagClass() {
      return {
        'tag-local': this.envInfo?.ui_tag === 'local',
        'tag-dev-server': this.envInfo?.ui_tag === 'dev-server'
      };
    }
  },
  async mounted() {
    try {
      const response = await fetch('/api/environment/');
      this.envInfo = await response.json();
    } catch (error) {
      console.error('Failed to fetch environment info:', error);
    }
  }
};
</script>

<style scoped>
.environment-tag {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 9999;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.tag-local {
  background-color: #4CAF50;
}

.tag-dev-server {
  background-color: #FF9800;
}
</style>
```

### Angular Example

```typescript
// environment-tag.component.ts
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

interface EnvironmentInfo {
  environment: string;
  platform: string;
  debug: boolean;
  version: string;
  ui_tag: string;
  show_tag: boolean;
}

@Component({
  selector: 'app-environment-tag',
  template: `
    <div *ngIf="envInfo?.show_tag" 
         class="environment-tag"
         [ngClass]="getTagClass()">
      {{ envInfo.ui_tag.toUpperCase() }}
    </div>
  `,
  styles: [`
    .environment-tag {
      position: fixed;
      top: 10px;
      right: 10px;
      z-index: 9999;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;
      color: white;
    }
    .tag-local { background-color: #4CAF50; }
    .tag-dev-server { background-color: #FF9800; }
  `]
})
export class EnvironmentTagComponent implements OnInit {
  envInfo: EnvironmentInfo | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<EnvironmentInfo>('/api/environment/')
      .subscribe(data => this.envInfo = data);
  }

  getTagClass() {
    return {
      'tag-local': this.envInfo?.ui_tag === 'local',
      'tag-dev-server': this.envInfo?.ui_tag === 'dev-server'
    };
  }
}
```

## CSS Styling Suggestions

```css
.environment-tag {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 9999;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  animation: fadeIn 0.3s ease-in;
}

.tag-local {
  background: linear-gradient(135deg, #4CAF50, #45a049);
}

.tag-dev-server {
  background: linear-gradient(135deg, #FF9800, #f57c00);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## Integration Tips

1. **Load early**: Fetch environment info during app initialization
2. **Cache**: Store the environment info in your app's state management
3. **Error handling**: Handle network failures gracefully
4. **Performance**: Only show the tag component when needed
5. **Accessibility**: Ensure proper contrast ratios for readability

## Testing

Test your implementation with these environment combinations:

- **Local Development**: `ui_tag: "local"`, `show_tag: true`
- **Railway Dev**: `ui_tag: "dev-server"`, `show_tag: true`  
- **Railway Production**: `ui_tag: null`, `show_tag: false`

## Health Check

Additional endpoint for monitoring: `/api/health/`

```json
{
  "status": "healthy",
  "environment": "development",
  "timestamp": "2025-07-08T19:28:00Z",
  "database": "connected"
}
```
