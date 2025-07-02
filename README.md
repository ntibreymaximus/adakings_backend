
# Adakings Backend API - Branch-Specific Versioning System

## Overview
This is the Adakings Backend API with a comprehensive **branch-specific versioning system**.

## Current Version Status


```
feature={self.get_version_from_file('feature')}
dev={self.get_version_from_file('dev')}
production={self.get_version_from_file('production')}
```

## Unified File Structure


```
{self.run_command('tree /F', shell=True).stdout}
```
