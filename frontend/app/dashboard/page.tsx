'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  FileText,
  MessageSquare,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getUser, type User } from '@/lib/auth';

interface StatCard {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
}

interface RecentActivity {
  id: string;
  type: 'source_upload' | 'episode_created' | 'user_login' | 'system_update';
  message: string;
  timestamp: string;
  user?: string;
}

const stats: StatCard[] = [
  {
    title: 'Total Sources',
    value: '24',
    change: '+3 this week',
    changeType: 'positive',
    icon: FileText,
  },
  {
    title: 'Active Episodes',
    value: '8',
    change: '+2 this week',
    changeType: 'positive',
    icon: MessageSquare,
  },
  {
    title: 'System Users',
    value: '12',
    change: '+1 this month',
    changeType: 'positive',
    icon: Users,
  },
  {
    title: 'Citation Coverage',
    value: '100%',
    change: 'Maintained',
    changeType: 'positive',
    icon: CheckCircle,
  },
];

const recentActivity: RecentActivity[] = [
  {
    id: '1',
    type: 'source_upload',
    message: 'New source uploaded: "Lincoln\'s Letters to Mary Todd"',
    timestamp: '2 hours ago',
    user: 'Admin User',
  },
  {
    id: '2',
    type: 'episode_created',
    message: 'Episode created: "Lincoln on Democracy"',
    timestamp: '4 hours ago',
    user: 'Host Demo',
  },
  {
    id: '3',
    type: 'user_login',
    message: 'User logged in: producer_demo',
    timestamp: '6 hours ago',
  },
  {
    id: '4',
    type: 'system_update',
    message: 'System health check completed successfully',
    timestamp: '1 day ago',
  },
];

const getActivityIcon = (type: RecentActivity['type']) => {
  switch (type) {
    case 'source_upload':
      return FileText;
    case 'episode_created':
      return MessageSquare;
    case 'user_login':
      return Users;
    case 'system_update':
      return Activity;
    default:
      return AlertCircle;
  }
};

const getActivityColor = (type: RecentActivity['type']) => {
  switch (type) {
    case 'source_upload':
      return 'text-blue-600 bg-blue-100';
    case 'episode_created':
      return 'text-green-600 bg-green-100';
    case 'user_login':
      return 'text-purple-600 bg-purple-100';
    case 'system_update':
      return 'text-gray-600 bg-gray-100';
    default:
      return 'text-red-600 bg-red-100';
  }
};

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const currentUser = getUser();
    setUser(currentUser);
  }, []);

  return (
    <DashboardLayout
      title="Dashboard"
      description="Welcome to They Might Say - Your AI-powered historical conversation system"
    >
      <div className="space-y-6">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-lincoln-600 to-lincoln-800 rounded-lg p-6 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">
                Welcome back, {user?.name || 'Administrator'}!
              </h2>
              <p className="text-lincoln-100">
                Your historical conversation system is running smoothly. 
                All citations are verified and ready for Studio Mode.
              </p>
            </div>
            <div className="hidden md:block">
              <div className="w-24 h-24 bg-white/10 rounded-full flex items-center justify-center">
                <TrendingUp className="w-12 h-12 text-white" />
              </div>
            </div>
          </div>
          
          <div className="mt-6 flex flex-wrap gap-4">
            <Button variant="secondary" size="sm">
              Start New Episode
            </Button>
            <Button variant="outline" size="sm" className="text-white border-white hover:bg-white/10">
              Upload Sources
            </Button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    {stat.title}
                  </CardTitle>
                  <stat.icon className="w-4 h-4 text-gray-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
                  <p className={`text-xs mt-1 ${
                    stat.changeType === 'positive' 
                      ? 'text-green-600' 
                      : stat.changeType === 'negative' 
                      ? 'text-red-600' 
                      : 'text-gray-500'
                  }`}>
                    {stat.change}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-2"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="w-5 h-5 mr-2" />
                  Recent Activity
                </CardTitle>
                <CardDescription>
                  Latest system events and user actions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity) => {
                    const Icon = getActivityIcon(activity.type);
                    const colorClass = getActivityColor(activity.type);
                    
                    return (
                      <div key={activity.id} className="flex items-start space-x-3">
                        <div className={`p-2 rounded-full ${colorClass}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900">{activity.message}</p>
                          <div className="flex items-center mt-1 text-xs text-gray-500">
                            <span>{activity.timestamp}</span>
                            {activity.user && (
                              <>
                                <span className="mx-1">•</span>
                                <span>{activity.user}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common tasks and shortcuts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full justify-start" variant="outline">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Start Studio Mode
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <FileText className="w-4 h-4 mr-2" />
                  Upload New Source
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Users className="w-4 h-4 mr-2" />
                  Manage Users
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Activity className="w-4 h-4 mr-2" />
                  System Health
                </Button>
              </CardContent>
            </Card>

            {/* System Status */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Database</span>
                    <span className="text-sm text-green-600 font-medium">Healthy</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Vector Search</span>
                    <span className="text-sm text-green-600 font-medium">Online</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">AI Service</span>
                    <span className="text-sm text-green-600 font-medium">Ready</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Citations</span>
                    <span className="text-sm text-green-600 font-medium">100% Coverage</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}