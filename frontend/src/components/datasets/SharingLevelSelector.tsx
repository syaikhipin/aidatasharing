'use client';

import { useState, useRef, useEffect } from 'react';
import { Lock, Users, Globe, ChevronDown } from 'lucide-react';

type SharingLevel = 'private' | 'organization' | 'public';

interface SharingLevelSelectorProps {
  currentLevel: SharingLevel;
  onLevelChange: (level: SharingLevel) => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const SHARING_LEVELS = [
  {
    value: 'private' as SharingLevel,
    label: 'Private',
    description: 'Only you can access this dataset',
    icon: Lock,
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    hoverColor: 'hover:bg-gray-200'
  },
  {
    value: 'organization' as SharingLevel,
    label: 'Organization',
    description: 'All members in your organization can access',
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    hoverColor: 'hover:bg-blue-200'
  },
  {
    value: 'public' as SharingLevel,
    label: 'Public',
    description: 'Anyone with the link can access',
    icon: Globe,
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    hoverColor: 'hover:bg-green-200'
  }
];

export function SharingLevelSelector({ 
  currentLevel, 
  onLevelChange, 
  disabled = false,
  size = 'md'
}: SharingLevelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState<'bottom' | 'top'>('bottom');
  const buttonRef = useRef<HTMLButtonElement>(null);
  
  const currentLevelData = SHARING_LEVELS.find(level => level.value === currentLevel);
  const CurrentIcon = currentLevelData?.icon || Lock;
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };
  
  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  // Calculate dropdown position based on available space
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const dropdownHeight = 280; // Approximate height of dropdown
      const spaceBelow = viewportHeight - buttonRect.bottom;
      const spaceAbove = buttonRect.top;
      
      // Position dropdown above if there's not enough space below
      if (spaceBelow < dropdownHeight && spaceAbove > dropdownHeight) {
        setDropdownPosition('top');
      } else {
        setDropdownPosition('bottom');
      }
    }
  }, [isOpen]);

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          ${sizeClasses[size]} 
          ${currentLevelData?.bgColor} 
          ${disabled ? 'opacity-50 cursor-not-allowed' : currentLevelData?.hoverColor + ' cursor-pointer'}
          inline-flex items-center space-x-2 rounded-md border border-gray-300 
          font-medium transition-colors duration-200 focus:outline-none focus:ring-2 
          focus:ring-blue-500 focus:border-transparent
        `}
      >
        <CurrentIcon className={`${iconSizes[size]} ${currentLevelData?.color}`} />
        <span className={currentLevelData?.color}>{currentLevelData?.label}</span>
        {!disabled && (
          <ChevronDown className={`${iconSizes[size]} ${currentLevelData?.color} transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        )}
      </button>

      {isOpen && !disabled && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-[9999]" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className={`
            absolute right-0 z-[10000] w-72 bg-white border border-gray-200 rounded-md shadow-xl
            ${dropdownPosition === 'bottom' ? 'mt-2' : 'mb-2 bottom-full'}
          `}>
            <div className="py-1">
              {SHARING_LEVELS.map((level) => {
                const Icon = level.icon;
                const isSelected = level.value === currentLevel;
                
                return (
                  <button
                    key={level.value}
                    onClick={() => {
                      onLevelChange(level.value);
                      setIsOpen(false);
                    }}
                    className={`
                      w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start space-x-3
                      ${isSelected ? 'bg-blue-50 border-r-2 border-blue-500' : ''}
                    `}
                  >
                    <Icon className={`h-5 w-5 mt-0.5 ${level.color}`} />
                    <div className="flex-1">
                      <div className={`font-medium ${level.color}`}>
                        {level.label}
                        {isSelected && (
                          <span className="ml-2 text-xs text-blue-600 font-normal">(Current)</span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {level.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
            
            {/* Footer */}
            <div className="border-t border-gray-200 px-4 py-2">
              <p className="text-xs text-gray-500">
                Changes take effect immediately. Public datasets can be accessed by anyone with the share link.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Helper function to get sharing level badge
export function SharingLevelBadge({ level, size = 'sm' }: { level: SharingLevel; size?: 'sm' | 'md' }) {
  const levelData = SHARING_LEVELS.find(l => l.value === level);
  if (!levelData) return null;
  
  const Icon = levelData.icon;
  const sizeClasses = size === 'sm' ? 'px-2 py-1 text-xs' : 'px-3 py-1 text-sm';
  const iconSize = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4';
  
  return (
    <span className={`
      ${sizeClasses} ${levelData.bgColor} ${levelData.color}
      inline-flex items-center space-x-1 rounded-full font-medium
    `}>
      <Icon className={iconSize} />
      <span>{levelData.label}</span>
    </span>
  );
}