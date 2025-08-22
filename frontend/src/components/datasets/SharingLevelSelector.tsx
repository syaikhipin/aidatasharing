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
  const [isAnimating, setIsAnimating] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const currentLevelData = SHARING_LEVELS.find(level => level.value === currentLevel);
  const CurrentIcon = currentLevelData?.icon || Lock;
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-1.5 text-sm',
    lg: 'px-3 py-2 text-base'
  };
  
  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-3.5 w-3.5',
    lg: 'h-4 w-4'
  };

  // Handle outside clicks and escape key
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
        buttonRef.current?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  // Calculate dropdown position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const dropdownHeight = 280; // Approximate height of dropdown
      const spaceBelow = viewportHeight - buttonRect.bottom;
      
      setDropdownPosition(spaceBelow < dropdownHeight ? 'top' : 'bottom');
    }
  }, [isOpen]);

  const handleLevelSelect = (level: SharingLevel) => {
    if (isAnimating || level === currentLevel) return;
    
    setIsAnimating(true);
    onLevelChange(level);
    setIsOpen(false);
    
    // Reset animation state after transition
    setTimeout(() => setIsAnimating(false), 200);
  };

  const handleToggle = () => {
    if (disabled || isAnimating) return;
    setIsOpen(!isOpen);
  };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        disabled={disabled || isAnimating}
        className={`
          ${sizeClasses[size]} 
          ${currentLevelData?.bgColor} 
          ${currentLevelData?.borderColor}
          ${disabled || isAnimating ? 'opacity-50 cursor-not-allowed' : currentLevelData?.hoverColor + ' cursor-pointer'}
          inline-flex items-center space-x-1.5 rounded-md border
          font-medium transition-all duration-150 focus:outline-none focus:ring-1 
          focus:ring-blue-400 focus:border-blue-400 shadow-sm min-w-0
        `}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleToggle();
          }
        }}
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
            absolute z-50 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl
            animate-in fade-in-0 zoom-in-95 duration-200
            ${dropdownPosition === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'}
          `}
          role="listbox"
        >
          <div className="py-1">
            {SHARING_LEVELS.map((level) => {
              const Icon = level.icon;
              const isSelected = level.value === currentLevel;
              
              return (
                <button
                  key={level.value}
                  onClick={() => handleLevelSelect(level.value)}
                  className={`
                    w-full px-4 py-4 text-left hover:bg-gray-50 flex items-start space-x-3
                    transition-colors duration-150 focus:outline-none focus:bg-blue-50
                    cursor-pointer select-none
                    ${isSelected ? 'bg-blue-50 border-r-4 border-blue-500' : ''}
                  `}
                  role="option"
                  aria-selected={isSelected}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleLevelSelect(level.value);
                    }
                  }}
                >
                  <Icon className={`h-3.5 w-3.5 mt-0.5 ${level.color} flex-shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className={`font-medium text-sm ${level.color} flex items-center gap-1.5`}>
                      {level.label}
                      {isSelected && (
                        <span className="text-xs text-blue-600 font-normal bg-blue-100 px-1.5 py-0.5 rounded">
                          ✓
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-600 mt-0.5 leading-relaxed">
                      {level.description}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
          
          {/* Footer */}
          <div className="border-t border-gray-100 px-3 py-2 bg-gray-50 rounded-b-md">
            <p className="text-xs text-gray-600 leading-snug">
              💡 Changes take effect immediately
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
      container: 'px-1.5 py-0.5 text-xs',
      icon: 'h-3 w-3'
    },
    md: {
      container: 'px-2 py-1 text-sm',
      icon: 'h-3.5 w-3.5'
    },
    lg: {
      container: 'px-2.5 py-1.5 text-sm',
      icon: 'h-4 w-4'
    }
  };
  
  const variant = sizeVariants[size];
  
  return (
    <span className={`
      ${variant.container} ${levelData.bgColor} ${levelData.color} ${levelData.borderColor}
      inline-flex items-center space-x-1 rounded-md font-medium border shadow-sm
    `}>
      <Icon className={variant.icon} />
      <span>{levelData.label}</span>
    </span>
  );
}