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
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    hoverColor: 'hover:bg-gray-200',
    borderColor: 'border-gray-300'
  },
  {
    value: 'organization' as SharingLevel,
    label: 'Organization',
    description: 'All members in your organization can access',
    icon: Users,
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    hoverColor: 'hover:bg-blue-200',
    borderColor: 'border-blue-300'
  },
  {
    value: 'public' as SharingLevel,
    label: 'Public',
    description: 'Anyone with the link can access',
    icon: Globe,
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    hoverColor: 'hover:bg-green-200',
    borderColor: 'border-green-300'
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
  const dropdownRef = useRef<HTMLDivElement>(null);
  
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

  // Calculate dropdown position and close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          buttonRef.current && !buttonRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
      
      // Calculate position
      if (buttonRef.current) {
        const buttonRect = buttonRef.current.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const dropdownHeight = 320; // Approximate height of dropdown
        const spaceBelow = viewportHeight - buttonRect.bottom;
        const spaceAbove = buttonRect.top;
        
        setDropdownPosition(spaceBelow < dropdownHeight && spaceAbove > dropdownHeight ? 'top' : 'bottom');
      }
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  const handleLevelSelect = (level: SharingLevel) => {
    onLevelChange(level);
    setIsOpen(false);
  };

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
          ${currentLevelData?.borderColor}
          ${disabled ? 'opacity-50 cursor-not-allowed' : currentLevelData?.hoverColor + ' cursor-pointer'}
          inline-flex items-center space-x-2 rounded-lg border
          font-medium transition-all duration-200 focus:outline-none focus:ring-2 
          focus:ring-blue-500 focus:border-blue-500 shadow-sm
        `}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <CurrentIcon className={`${iconSizes[size]} ${currentLevelData?.color}`} />
        <span className={`${currentLevelData?.color} font-medium`}>{currentLevelData?.label}</span>
        {!disabled && (
          <ChevronDown className={`${iconSizes[size]} ${currentLevelData?.color} transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        )}
      </button>

      {isOpen && !disabled && (
        <div 
          ref={dropdownRef}
          className={`
            fixed z-[99999] w-80 bg-white border border-gray-200 rounded-lg shadow-xl
            animate-in fade-in-0 zoom-in-95 duration-200
          `}
          style={{
            top: dropdownPosition === 'bottom' 
              ? (buttonRef.current?.getBoundingClientRect().bottom ?? 0) + 8 
              : (buttonRef.current?.getBoundingClientRect().top ?? 0) - 320 - 8,
            left: Math.max(8, (buttonRef.current?.getBoundingClientRect().right ?? 0) - 320),
            maxHeight: '400px',
            overflowY: 'auto'
          }}
          role="listbox"
        >
          <div className="py-2">
            {SHARING_LEVELS.map((level) => {
              const Icon = level.icon;
              const isSelected = level.value === currentLevel;
              
              return (
                <button
                  key={level.value}
                  onClick={() => handleLevelSelect(level.value)}
                  className={`
                    w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start space-x-3
                    transition-colors duration-150 focus:outline-none focus:bg-blue-50
                    ${isSelected ? 'bg-blue-50 border-r-4 border-blue-500' : ''}
                  `}
                  role="option"
                  aria-selected={isSelected}
                >
                  <Icon className={`${iconSizes.md} mt-0.5 ${level.color} flex-shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className={`font-medium ${level.color} flex items-center gap-2`}>
                      {level.label}
                      {isSelected && (
                        <span className="text-xs text-blue-600 font-normal bg-blue-100 px-2 py-0.5 rounded-full">
                          Current
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mt-1 leading-relaxed">
                      {level.description}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
          
          {/* Footer */}
          <div className="border-t border-gray-100 px-4 py-3 bg-gray-50 rounded-b-lg">
            <p className="text-xs text-gray-600 leading-relaxed">
              💡 Changes take effect immediately. Public datasets can be accessed by anyone with the share link.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Enhanced sharing level badge component
export function SharingLevelBadge({ level, size = 'sm' }: { level: SharingLevel; size?: 'sm' | 'md' | 'lg' }) {
  const levelData = SHARING_LEVELS.find(l => l.value === level);
  if (!levelData) return null;
  
  const Icon = levelData.icon;
  
  const sizeVariants = {
    sm: {
      container: 'px-2 py-1 text-xs',
      icon: 'h-3 w-3'
    },
    md: {
      container: 'px-3 py-1.5 text-sm',
      icon: 'h-4 w-4'
    },
    lg: {
      container: 'px-4 py-2 text-base',
      icon: 'h-5 w-5'
    }
  };
  
  const variant = sizeVariants[size];
  
  return (
    <span className={`
      ${variant.container} ${levelData.bgColor} ${levelData.color} ${levelData.borderColor}
      inline-flex items-center space-x-1.5 rounded-full font-medium border shadow-sm
    `}>
      <Icon className={variant.icon} />
      <span>{levelData.label}</span>
    </span>
  );
}