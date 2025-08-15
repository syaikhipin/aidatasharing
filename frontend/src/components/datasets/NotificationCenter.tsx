'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { dataAccessAPI } from '@/lib/api';

interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  related_resource_type?: string;
  related_resource_id?: number;
  created_at: string;
  sender_name?: string;
}

interface NotificationCenterProps {
  className?: string;
}

export function NotificationCenter({ className = '' }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'access_requests'>('all');

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await dataAccessAPI.getNotifications();
      setNotifications(response || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      await dataAccessAPI.markNotificationAsRead(notificationId);
      setNotifications(prev => 
        prev.map(notif => 
          notif.id === notificationId 
            ? { ...notif, is_read: true }
            : notif
        )
      );
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await dataAccessAPI.markAllNotificationsAsRead();
      setNotifications(prev => 
        prev.map(notif => ({ ...notif, is_read: true }))
      );
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const deleteNotification = async (notificationId: number) => {
    try {
      await dataAccessAPI.deleteNotification(notificationId);
      setNotifications(prev => prev.filter(notif => notif.id !== notificationId));
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const handleApprovalAction = async (notificationId: number, requestId: number, action: 'approve' | 'reject') => {
    try {
      await dataAccessAPI.approveAccessRequest(requestId, {
        decision: action,
        reason: action === 'reject' ? 'Rejected via notification center' : 'Approved via notification center'
      });
      
      // Mark notification as read and remove it
      await markAsRead(notificationId);
      setNotifications(prev => prev.filter(notif => notif.id !== notificationId));
      
      // Show success message
      console.log(`Access request ${action}ed successfully`);
    } catch (error) {
      console.error(`Error ${action}ing access request:`, error);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'info': return 'ℹ️';
      case 'access_request': return '🔑';
      default: return '📢';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return 'border-green-200 bg-green-50';
      case 'warning': return 'border-yellow-200 bg-yellow-50';
      case 'error': return 'border-red-200 bg-red-50';
      case 'info': return 'border-blue-200 bg-blue-50';
      case 'access_request': return 'border-purple-200 bg-purple-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const filteredNotifications = notifications.filter(notif => {
    switch (filter) {
      case 'unread': return !notif.is_read;
      case 'access_requests': return notif.related_resource_type === 'access_request';
      default: return true;
    }
  });

  const unreadCount = notifications.filter(notif => !notif.is_read).length;

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <div className="flex flex-col items-center space-y-2">
              <div className="w-8 h-8 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
              <p className="text-sm text-gray-600">Loading notifications...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <span>Notifications</span>
              {unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  {unreadCount}
                </span>
              )}
            </CardTitle>
            <CardDescription>
              Stay updated on your access requests and system notifications
            </CardDescription>
          </div>
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={markAllAsRead}
            >
              Mark all read
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Filter Tabs */}
        <div className="flex space-x-1 mb-4 bg-gray-100 rounded-lg p-1">
          {[
            { key: 'all', label: 'All', count: notifications.length },
            { key: 'unread', label: 'Unread', count: unreadCount },
            { key: 'access_requests', label: 'Access Requests', count: notifications.filter(n => n.related_resource_type === 'access_request').length }
          ].map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setFilter(key as any)}
              className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                filter === key
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {label} {count > 0 && `(${count})`}
            </button>
          ))}
        </div>

        {/* Notifications List */}
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">📭</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No notifications</h3>
            <p className="text-gray-600">
              {filter === 'unread' 
                ? "You're all caught up! No unread notifications."
                : filter === 'access_requests'
                ? "No access request notifications."
                : "No notifications to display."
              }
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`border rounded-lg p-4 transition-all ${
                  notification.is_read 
                    ? 'border-gray-200 bg-white' 
                    : `${getNotificationColor(notification.notification_type)} border-l-4`
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-lg">
                        {getNotificationIcon(notification.notification_type)}
                      </span>
                      <h4 className={`font-medium ${
                        notification.is_read ? 'text-gray-700' : 'text-gray-900'
                      }`}>
                        {notification.title}
                      </h4>
                      {!notification.is_read && (
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                      )}
                    </div>
                    <p className={`text-sm mb-2 ${
                      notification.is_read ? 'text-gray-600' : 'text-gray-700'
                    }`}>
                      {notification.message}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>
                        {new Date(notification.created_at).toLocaleString()}
                      </span>
                      {notification.sender_name && (
                        <span>From: {notification.sender_name}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {/* Approval actions for access requests */}
                    {notification.related_resource_type === 'access_request' && notification.related_resource_id && !notification.is_read && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleApprovalAction(notification.id, notification.related_resource_id!, 'approve')}
                          className="text-green-600 hover:text-green-700 border-green-300 hover:bg-green-50"
                        >
                          ✓ Approve
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleApprovalAction(notification.id, notification.related_resource_id!, 'reject')}
                          className="text-red-600 hover:text-red-700 border-red-300 hover:bg-red-50"
                        >
                          ✗ Reject
                        </Button>
                      </>
                    )}
                    {!notification.is_read && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => markAsRead(notification.id)}
                      >
                        Mark read
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deleteNotification(notification.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}