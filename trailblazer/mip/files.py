# -*- coding: utf-8 -*-
"""Parse the MIP config file."""
import csv
from typing import TextIO

PED_SEX_MAP = {1: 'male', 2: 'female', 0: 'unknown'}


def safe_list_get(a_list, idx, default=None):
    """Method to safely read values from a list"""
    try:
        return a_list[idx]
    except IndexError:
        return default


def parse_config(data: dict) -> dict:
    """Parse MIP config file.

    Args:
        data (dict): raw YAML input from MIP analysis config file

    Returns:
        dict: parsed data
    """
    return {
        'email': data.get('email'),
        'family': data.get('family_id'),
        'samples': [{
            'id': sample_id,
            'type': analysis_type,
        } for sample_id, analysis_type in data['analysis_type'].items()],
        'config_path': data.get('config_file_analysis'),
        'is_dryrun': True if 'dry_run_all' in data else False,
        'log_path': data.get('log_file'),
        'out_dir': data.get('outdata_dir'),
        'priority': data.get('slurm_quality_of_service'),
        'sampleinfo_path': data.get('sample_info_file'),
    }


def parse_sampleinfo(data: dict) -> dict:
    """Parse MIP sample info file.

    Args:
        data (dict): raw YAML input from MIP qc sample info file

    Returns:
        dict: parsed data
    """

    genome_build = data.get('human_genome_build')
    genome_build_str = f"{genome_build.get('source')}{genome_build.get('version')}"
    if 'svdb' in data['program']:
        svdb_outpath = (f"{data['program']['svdb'].get('path')}")
    else:
        svdb_outpath = ''
    outdata = {
        'date': data.get('analysis_date'),
        'family': data.get('family'),
        'genome_build': genome_build_str,
        'rank_model_version': data.get('program', {}).get('genmod', {}).get('rank_model', {}).get(
            'version'),
        'is_finished': data.get('analysisrunstatus') == 'finished',
        'pedigree_path': data.get('pedigree_minimal'),
        'peddy': {
            'ped': (data.get('program', {}).get('peddy', {}).get('peddy', {}).get('path') if
                    'peddy' in data['program'] else None),
            'ped_check': (data.get('program', {}).get('peddy', {}).get('ped_check',
                                                                       {}).get('path') if
                          'peddy' in data['program'] else None),
            'sex_check': (data.get('program', {}).get('peddy', {}).get('sex_check',
                                                                       {}).get('path') if
                          'peddy' in data['program'] else None),
        },
        'qcmetrics_path': data.get('program', {}).get('qccollect', {}).get('path'),
        'samples': [],
        'snv': {
            'bcf': data.get('most_complete_bcf', {}).get('path'),
            'clinical_vcf': data.get('vcf_binary_file', {}).get('clinical', {}).get('path'),
            'gbcf': data.get('gbcf_file', {}).get('path'),
            'research_vcf': data.get('vcf_binary_file', {}).get('research', {}).get('path'),
        },
        'svdb_outpath': svdb_outpath,
        'sv': {
            'bcf': data.get('sv_bcf_file', {}).get('path'),
            'clinical_vcf': (data.get('sv_vcf_binary_file', {}).get('clinical', {}).get('path') if
                             'sv_vcf_binary_file' in data else None),
            'merged': svdb_outpath,
            'research_vcf': (data.get('sv_vcf_binary_file', {}).get('research', {}).get('path') if
                             'sv_vcf_binary_file' in data else None),
        },
        'version': data.get('mip_version'),
    }

    for sample_id, sample_data in data['sample'].items():
        sample = {
            'id': sample_id,
            'bam': sample_data.get('most_complete_bam', {}).get('path'),
            'sambamba': safe_list_get(list(sample_data.get('program', {}).get('sambamba_depth',
                                                                              {}).values()), 0,
                                      {}).get('path'),
            'sex': sample_data.get('sex'),
            # subsample mt is only for wgs data
            'subsample_mt': (safe_list_get(list(sample_data.get('program', {}).get(
                'samtools_subsample_mt', {})
                                                .values()), 0, {}).get('path') if
                             'samtools_subsample_mt' in sample_data['program'] else None),
            'vcf2cytosure': safe_list_get(list(sample_data.get('program', {}).get('vcf2cytosure',
                                                                                  {}).values()),
                                          0, {}).get('path'),
        }
        chanjo_sexcheck = safe_list_get(list(sample_data.get('program', {}).get(
            'chanjo_sexcheck', {}).values()), 0)
        sample['chanjo_sexcheck'] = chanjo_sexcheck.get('path')
        outdata['samples'].append(sample)

    return outdata


def parse_qcmetrics(metrics: dict) -> dict:
    """Parse MIP qc metrics file.
    Args:
        metrics (dict): raw YAML input from MIP qc metrics file

    Returns:
        dict: parsed data
    """
    data = {
        'versions': {
            'freebayes': metrics.get('program', {}).get('freebayes', {}).get('version'),
            'gatk': metrics.get('program', {}).get('gatk', {}).get('version'),
            'manta': metrics.get('program', {}).get('manta', {}).get('version'),
            'bcftools': metrics.get('program', {}).get('bcftools', {}).get('version'),
            'vep': metrics.get('program', {}).get('varianteffectpredictor', {}).get('version'),
        },
        'samples': [],
    }

    plink_samples = {}
    plink_sexcheck = metrics.get('program', {}).get('plink_sexcheck', {}).get('sample_sexcheck')
    if isinstance(plink_sexcheck, str):
        sample_id, sex_number = plink_sexcheck.strip().split(':', 1)
        plink_samples[sample_id] = PED_SEX_MAP.get(int(sex_number))
    elif isinstance(plink_sexcheck, list):
        for sample_raw in plink_sexcheck:
            sample_id, sex_number = sample_raw.split(':', 1)
            plink_samples[sample_id] = PED_SEX_MAP.get(int(sex_number))

    for sample_id, sample_metrics in metrics['sample'].items():
        ## Bam stats metrics
        bam_stats = [values['bamstats'] for key, values in sample_metrics.items()
                     if key[:-1].endswith('.lane')]
        total_reads = sum(int(bam_stat['raw_total_sequences']) for bam_stat in bam_stats)
        total_mapped = sum(int(bam_stat['reads_mapped']) for bam_stat in bam_stats)

        ## Picard metrics
        main_key = [key for key in sample_metrics.keys() if '_lanes_' in key][0]

        hs_metrics = sample_metrics[main_key]['collecthsmetrics']['header']['data']
        multiple_inst_metrics = sample_metrics[main_key]['collectmultiplemetricsinsertsize'][
            'header']['data']
        multiple_metrics = sample_metrics[main_key]['collectmultiplemetrics']['header']['pair']

        sample_data = {
            'at_dropout': hs_metrics.get('AT_DROPOUT'),
            'completeness_target': {
                10: hs_metrics.get('PCT_TARGET_BASES_10X'),
                20: hs_metrics.get('PCT_TARGET_BASES_20X'),
                50: hs_metrics.get('PCT_TARGET_BASES_50X'),
                100: hs_metrics.get('PCT_TARGET_BASES_100X'),
            },
            'duplicates': float(sample_metrics[main_key]['markduplicates']['fraction_duplicates']),
            'gc_dropout': hs_metrics.get('GC_DROPOUT'),
            'id': sample_id,
            'median_insert_size': multiple_inst_metrics.get('MEDIAN_INSERT_SIZE'),
            'mapped': total_mapped / total_reads,
            'plink_sex': plink_samples.get(sample_id),
            'predicted_sex': sample_metrics[main_key]['chanjo_sexcheck'].get('gender'),
            'reads': total_reads,
            'insert_size_standard_deviation': float(multiple_inst_metrics['STANDARD_DEVIATION']),
            'strand_balance': float(multiple_metrics['STRAND_BALANCE']),
            'target_coverage': float(hs_metrics['MEAN_TARGET_COVERAGE']),
        }
        data['samples'].append(sample_data)
    return data


def parse_peddy_sexcheck(handle: TextIO):
    """Parse Peddy sexcheck output."""
    data = {}
    samples = csv.DictReader(handle)
    for sample in samples:
        data[sample['sample_id']] = {
            'predicted_sex': sample.get('predicted_sex'),
            'het_ratio': float(sample['het_ratio']),
            'error': True if sample['error'] == 'True' else False,
        }
    return data


def parse_chanjo_sexcheck(handle: TextIO):
    """Parse Chanjo sex-check output."""
    samples = csv.DictReader(handle, delimiter='\t')
    for sample in samples:
        return {
            'predicted_sex': sample.get('sex'),
            'x_coverage': float(sample['#X_coverage']),
            'y_coverage': float(sample['Y_coverage']),
        }
