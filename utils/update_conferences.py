#!/usr/bin/env python3
# coding: utf-8

# Compare and Update Conference Data Structure
# This script:
# 1. Updates the conferences.yml file with new fields from paperswithcode while maintaining backward compatibility
# 2. Optionally merges data from paperswithcode conferences into our format
# 
# New fields include: full_name, start, end, abstract_deadline, hindex, paperslink, pwclink

import yaml
import sys
import os
import argparse
from collections import OrderedDict
from shutil import copyfile

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from yaml.representer import SafeRepresenter
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

Dumper.add_representer(OrderedDict, dict_representer)
Loader.add_constructor(_mapping_tag, dict_constructor)

Dumper.add_representer(str, SafeRepresenter.represent_str)

def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)

def load_conferences(file_path):
    """Load conference data from YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as stream:
            try:
                return yaml.load(stream, Loader=Loader)
            except yaml.YAMLError as exc:
                print(f"Error loading conferences: {exc}")
                return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None

def save_conferences(conferences, file_path):
    """Save conference data to YAML file with proper formatting."""
    with open(file_path, 'w', encoding='utf-8') as outfile:
        for line in ordered_dump(
                conferences,
                Dumper=yaml.SafeDumper,
                default_flow_style=False,
                explicit_start=True).splitlines():
            outfile.write('\n')
            outfile.write(line.replace('- title:', '\n- title:'))

def update_structure(conferences):
    """Add new fields to conferences data structure if they don't exist."""
    new_fields = ['full_name', 'start', 'end', 'abstract_deadline', 'hindex', 'paperslink', 'pwclink']
    
    updated_count = 0
    for conf in conferences:
        updated = False
        for field in new_fields:
            if field not in conf:
                conf[field] = None
                updated = True
        
        if updated:
            updated_count += 1
    
    return updated_count

def compare_structures(our_conferences, pwc_conferences):
    """Compare structures of our conferences and paperswithcode conferences."""
    if not our_conferences or not pwc_conferences:
        print("Cannot compare structures: one or both of the conference sources are empty.")
        return
    
    # Get all fields from our conferences
    our_fields = set()
    for conf in our_conferences:
        our_fields.update(conf.keys())
    
    # Get all fields from paperswithcode conferences
    pwc_fields = set()
    for conf in pwc_conferences:
        pwc_fields.update(conf.keys())
    
    print("=== Structure Comparison ===")
    print(f"Our fields ({len(our_fields)}):")
    for field in sorted(our_fields):
        print(f"  - {field}")
    
    print(f"\nPapersWithCode fields ({len(pwc_fields)}):")
    for field in sorted(pwc_fields):
        print(f"  - {field}")
    
    print("\nFields only in our conferences:")
    for field in sorted(our_fields - pwc_fields):
        print(f"  - {field}")
    
    print("\nFields only in PapersWithCode:")
    for field in sorted(pwc_fields - our_fields):
        print(f"  - {field}")

def find_matching_conferences(our_conf, pwc_conferences):
    """Find matching conferences in PapersWithCode data by title and year."""
    matches = []
    
    # Try to match by title and year
    title = our_conf.get('title', '').lower().strip()
    year = str(our_conf.get('year', '')).strip()
    
    for pwc_conf in pwc_conferences:
        pwc_title = pwc_conf.get('title', '').lower().strip()
        pwc_year = str(pwc_conf.get('year', '')).strip()
        
        if title == pwc_title and year == pwc_year:
            matches.append(pwc_conf)
    
    return matches

def merge_data(our_conferences, pwc_conferences, dry_run=True):
    """Merge data from paperswithcode into our conferences."""
    if not our_conferences or not pwc_conferences:
        print("Cannot merge data: one or both of the conference sources are empty.")
        return our_conferences
    
    fields_to_merge = ['full_name', 'hindex', 'start', 'end', 'abstract_deadline', 'paperslink', 'pwclink']
    updated_conferences = []
    update_count = 0
    
    for our_conf in our_conferences:
        matches = find_matching_conferences(our_conf, pwc_conferences)
        
        if matches:
            if len(matches) > 1:
                print(f"Warning: Multiple matches found for {our_conf['title']} {our_conf['year']}")
            
            # Take the first match
            pwc_conf = matches[0]
            
            # Map fields from pwc_conf to our_conf
            updated = False
            for field in fields_to_merge:
                pwc_field = field
                
                # Handle field name differences
                if field == 'paperslink':
                    pwc_field = 'url_papers'
                elif field == 'pwclink':
                    pwc_field = 'url_pwc'
                
                if pwc_field in pwc_conf and pwc_conf[pwc_field]:
                    if field not in our_conf or our_conf[field] is None:
                        if not dry_run:
                            our_conf[field] = pwc_conf[pwc_field]
                        updated = True
                        print(f"  - Adding {field}='{pwc_conf[pwc_field]}' to {our_conf['title']} {our_conf['year']}")
            
            if updated:
                update_count += 1
        
        updated_conferences.append(our_conf)
    
    print(f"\nUpdated {update_count} conferences{' (dry run)' if dry_run else ''}.")
    return updated_conferences

def main():
    parser = argparse.ArgumentParser(description='Update conference data structure and optionally merge data from paperswithcode.')
    parser.add_argument('--update-only', action='store_true', help='Only update the structure without merging data')
    parser.add_argument('--pwc', type=str, help='Path to paperswithcode conferences YAML file')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing to file')
    args = parser.parse_args()
    
    # Source and output files
    source_file = "../_data/conferences.yml"
    backup_file = "../_data/conferences.yml.bak"
    output_file = "../_data/conferences.yml"
    
    print(f"Loading conferences from {source_file}...")
    our_conferences = load_conferences(source_file)
    
    if our_conferences:
        print(f"Loaded {len(our_conferences)} conferences.")
        
        # Create backup if not in dry-run mode
        if not args.dry_run:
            print(f"Creating backup at {backup_file}...")
            copyfile(source_file, backup_file)
        
        # Update structure
        updated_count = update_structure(our_conferences)
        print(f"Updated structure for {updated_count} conferences.")
        
        # Merge with paperswithcode data if provided
        if not args.update_only and args.pwc:
            print(f"\nLoading paperswithcode conferences from {args.pwc}...")
            pwc_conferences = load_conferences(args.pwc)
            
            if pwc_conferences:
                print(f"Loaded {len(pwc_conferences)} paperswithcode conferences.")
                
                # Compare structures
                compare_structures(our_conferences, pwc_conferences)
                
                # Merge data
                print("\n=== Merging Data ===")
                our_conferences = merge_data(our_conferences, pwc_conferences, dry_run=args.dry_run)
        
        # Save updated conferences if not in dry-run mode
        if not args.dry_run:
            print(f"\nSaving updated conferences to {output_file}...")
            save_conferences(our_conferences, output_file)
            print("Done!")
        else:
            print("\nDry run - no changes were written to files.")
    else:
        print("Failed to load conferences data.")
        sys.exit(1)

if __name__ == "__main__":
    main()