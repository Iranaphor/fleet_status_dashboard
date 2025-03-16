#!/usr/bin/env python3
import os
import sys
import yaml
import time
import datetime
import threading
import subprocess
import paho.mqtt.client as mqtt


def git_status(repo_config):
    """
    Run 'git status' in the specified repo directory.
    Returns the output or error.
    """
    repo_dir = repo_config.get('dir')
    try:
        result = subprocess.run(
            ['git', 'status'],
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            result = result.stdout.strip()

            # Check which line is relevent
            if 'Your branch is ahead' in result:
                return 'ahead'
            elif 'Your branch is up-to-date' in result:
                return 'up-to-date'
            return result

        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"


def git_branch(repo_config):
    """
    Run 'git status' in the specified repo directory.
    Returns the branch of it.
    """
    repo_dir = repo_config.get('dir')
    try:
        result = subprocess.run(
            ['git', 'branch'],
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:

            result = result.stdout.strip()
            result = [r for r in result.split('\n') if '*' in r][0]
            result = result.replace('* ', '')
            return result

        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"


def git_remote_name(repo_config):
    """
    Run 'git status' in the specified repo directory.
    Returns the output or error.
    """
    repo_dir = repo_config.get('dir')
    try:
        result = subprocess.run(
            ['git', 'status'],
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            result = result.stdout.strip()

            # Check which line is relevent
            result = result.split('Your branch')[1].split('/')[0].split("'")[1]
            return result

        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"


def git_remote(repo_config):
    """
    Run 'git remote -v' in the specified repo directory.
    Returns the branch of it.
    """
    repo_dir = repo_config.get('dir')
    try:
        remote_name = git_remote_name(repo_config)
        result = subprocess.run(
            ['git', 'remote', '-v'],
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:

            result = result.stdout.strip()
            result = [r for r in result.split('\n') if 'fetch' in r and remote_name in r][0]
            result = result.split('http')[0].strip()
            return result

        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"




def robot_name(repo_config):
    robot_name = os.getenv('ROBOT_NAME', 'default_robot')
    return robot_name

def battery(repo_config):
    return ''

def last_online(repo_config):
    now = datetime.datetime.now()
    return now.strftime("%d-%b-%Y %H:%M")
