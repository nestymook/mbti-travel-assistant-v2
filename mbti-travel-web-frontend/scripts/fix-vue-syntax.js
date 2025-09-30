#!/usr/bin/env node

/**
 * Fix Vue syntax errors - remove invalid </template> tags after </style>
 */

import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

console.log('🔧 Fixing Vue syntax errors...');

// Get all Vue files with the syntax error
const files = [
  'src/components/itinerary/structured/TimeInputsComponent.vue',
  'src/components/itinerary/structured/ImportantCheckboxesComponent.vue',
  'src/components/itinerary/layouts/ISFJLayout.vue',
  'src/components/itinerary/layouts/ISTJLayout.vue',
  'src/components/itinerary/layouts/ISFPLayout.vue',
  'src/components/itinerary/layouts/INFJLayout.vue',
  'src/components/itinerary/layouts/INTJLayout.vue',
  'src/components/itinerary/layouts/ESFJLayout.vue',
  'src/components/itinerary/layouts/ENFPLayout.vue',
  'src/components/itinerary/layouts/ENTJLayout.vue',
  'src/components/itinerary/flexible/PointFormComponent.vue',
  'src/components/itinerary/flexible/FlashyStylingComponent.vue',
  'src/components/itinerary/feeling/WarmThemeComponent.vue',
  'src/components/itinerary/feeling/SocialSharingComponent.vue',
  'src/components/itinerary/flexible/CasualLayoutComponent.vue',
  'src/components/itinerary/feeling/GroupNotesComponent.vue',
  'src/components/itinerary/feeling/DescriptionsComponent.vue',
  'src/components/itinerary/colorful/VibrantThemeComponent.vue',
  'src/components/itinerary/colorful/ImagePlaceholdersComponent.vue',
  'src/components/itinerary/colorful/GradientBackgroundsComponent.vue',
  'src/components/itinerary/colorful/CreativeLayoutComponent.vue'
];

let fixedCount = 0;

for (const file of files) {
  try {
    const content = readFileSync(file, 'utf8');
    
    // Fix the syntax error by removing </template> after </style>
    const fixedContent = content.replace(/(<\/style>\s*)\n<\/template>/g, '$1');
    
    if (content !== fixedContent) {
      writeFileSync(file, fixedContent);
      console.log(`✅ Fixed: ${file}`);
      fixedCount++;
    }
  } catch (error) {
    console.warn(`⚠️  Could not fix ${file}:`, error.message);
  }
}

console.log(`🎉 Fixed ${fixedCount} Vue files`);