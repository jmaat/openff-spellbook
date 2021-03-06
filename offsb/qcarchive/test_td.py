#!/usr/bin/env python3
import offsb.tools.const as const
import pickle
import numpy as np
import matplotlib.pyplot as plt


def select_param( lbl):
    oFF_param = None

    letter = lbl[0]
    if letter == 'b':
        oFF_param = "Bonds"
    elif letter == 'a':
        oFF_param = 'Angles'
    elif letter == 't':
        oFF_param = "ProperTorsions"
    elif letter == 'i':
        oFF_param = "ImproperTorsions"
    elif letter == 'n':
        oFF_param = "vdW"
    
    return oFF_param

def plot_displacement( ax, dat, label_obj, displacement_fn=None):

    label = label_obj.get( "id")

    if displacement_fn is None:
        if 'b' in label:
            displacement_fn = bond_disp
        elif 'a' in label:
            displacement_fn = angle_disp

    if displacement_fn is not None:
        kT = (.001987*298.15)
        equil, delta = displacement_fn( label_obj, thresh=kT)

        color='blue'
        if((dat < (equil - delta)).any() or (dat > (equil + delta)).any()):
            color='red'
            #print(label + "= R", end=" ")
        elif(dat.max() < equil or dat.min() > equil):
            #print(label + "= Y", end=" ")
            color='yellow'
        else:
            color='green'
        ax.axhline(y=equil, ls='-', marker='.', color='black', ms=20, mec='black', mfc=color)
        ax.axhline(y=equil + delta, ls='--', marker='.', color='black', ms=10, mec='black', mfc=color)
        ax.axhline(y=equil - delta, ls='--', marker='.', color='black', ms=10, mec='black', mfc=color)
        ax.axhline(y=equil, ls='-', marker='.', color='black', ms=20, mec='black', mfc=color)
        ax.axhline(y=equil + delta, ls='--', marker='.', color='black', ms=10, mec='black', mfc=color)
        ax.axhline(y=equil - delta, ls='--', marker='.', color='black', ms=10, mec='black', mfc=color)

def select_data_of_oFFlabel_from_td(QCAtree, oFFtree, datatree, query, entry=None, verbose=False):
    
    oFF_param = select_param( query)

    hits = []
    angles = []
    result = []
    visited = set()
#    iter_fn = node_iter_torsiondriverecord_minimum

    if entry is None:
        entries = QCAtree.iter_entry()
    elif not hasattr( entry, "__iter__"):
        entries = [entry]
    else:
        entries = entry
    for entry in entries:
        ID = entry.index
        obj = QCAtree.db.get( entry.payload)
        smiles = obj.get( "entry").attributes.get( "canonical_smiles")
        status = obj.get( "data").get( "status")[:]
        oFFobj = oFFtree.db.get( entry.payload)
        labels = oFFobj.get( "data")
        found = False
        #for mol in QCAtree.node_iter_optimization_minimum( entry, select="Molecule"):
        for mol in QCAtree.node_iter_torsiondriverecord_minimum( entry, select="Molecule"):
            if mol.index in visited:
                continue
            visited.add(mol.index)
            for pair, label in labels.get( oFF_param).items():
                #print( pair, label)
                if label != query:
                    continue

                dobj = datatree.db.get( mol.payload)
                angle = eval(list( QCAtree.node_iter_to_root( mol, select="Constraint"))[0].payload)[0]
                molid = mol.index
                assert mol.index in [ x.index for x in QCAtree.node_iter_to_root( mol)]

                vals = dobj.get( pair)
                result.append([ID, molid, query, pair, angle, vals, smiles])
                pair="-".join([str(k) for k in pair])  
                if verbose:
                    print("Entry({:11s}) {:16s} {:16s} {} {:4s} {:4.0f} {} {:64s}".format( status, ID, molid, pair, query, angle, vals, smiles))

    return result

def bond_disp( obj, thresh=1.0):
    force_k = obj.get( "k")
    force_k = force_k / force_k.unit
    length = obj.get( "length")
    length = length / length.unit
    delta = (2*(thresh)/force_k)**.5
    return length, delta

def angle_disp( obj, thresh=1.0):
    force_k = obj.get( "k")
    force_k = force_k / force_k.unit
    length = obj.get( "angle")
    length = length / length.unit
    delta = (2*(thresh)/force_k)**.5
    return length, delta

#def torsion_disp( obj, thresh=1.0):
#    force_k = obj.get( "k")
#    force_k = force_k / force_k.unit
#    length = obj.get( "angle")
#    length = length / length.unit
#    delta = (2*(thresh)/force_k)**.5
#    return length, delta

def plot_td_all_minima( ang, vals, label_obj, displacement_fn=None):
    """
    plots torsiondrive data of all optimizations (does not connect points)
    """
    rows = 1
    fig = plt.figure(figsize=(8,4*rows),dpi=120)
    ax_grid = []
    for r in range(rows):
        ax = [plt.subplot2grid((rows,3),(r,0), colspan=2, fig=fig)]
        ax.append(plt.subplot2grid((rows,3),(r,2), fig=fig, sharey=ax[0]))
        ax_grid.append(ax)

    label = label_obj.get( "id")
    ax_grid[0][0].plot(ang, vals, lw=0, ls='-', marker='.' , label=label, ms=2)
    ax_grid[0][0].legend(loc='upper right')

    ax_grid[0][1].hist(vals,bins=100, histtype='step', orientation='horizontal')
    
    plot_displacement( ax_grid[0][0], vals, label_obj, displacement_fn)
    plot_displacement( ax_grid[0][1], vals, label_obj, displacement_fn)
    return fig

def plot_td_minima( ang, vals, atoms, label_obj, molid=None, displacement_fn=None):
    """
    plots the lowest energy torsiondrive, using the optimizations which gave the lowest energy
    atoms should be [( molid, *group)]
    molid will only plot those which match e.g. ['2', '3', '4']
    """
    import matplotlib.pyplot as plt
    import numpy as np
    rows = 1
    fig = plt.figure(figsize=(8,4*rows),dpi=120)
    ax_grid = []
    for r in range(rows):
        ax = [plt.subplot2grid((rows,3),(r,0), colspan=2, fig=fig)]
        ax.append(plt.subplot2grid((rows,3),(r,2), fig=fig, sharey=ax[0]))
        ax_grid.append(ax) 
    label = label_obj.get( "id")
    labels = set()
    #print(ang[0])
    color='blue'
    if molid is not None:
        if not hasattr( molid, "__iter__"):
            molid = [molid]

    def gen_subset( ang, vals, mask):
        ang_i = ang[ mask ]
        vals_i = vals[ mask ]
        srt = np.argsort(ang_i)
        ang_i = ang_i[srt]
        vals_i = vals_i[srt]
        return ang_i, vals_i

    for group in atoms:
        if (molid is not None) and (group[0] not in molid):
            continue

        mask = [x == group for x in atoms]
        ang_i, vals_i = gen_subset( ang, vals, mask)

        thislabel = label
        if thislabel in labels:
            thislabel=""
        labels.add(label)    
        ax_grid[0][0].plot(ang_i, vals_i, lw=0.1, ls='-', marker='.' , color=color, label=thislabel, ms=2, alpha=.3)
        
    ax_grid[0][0].legend(loc='upper right')
    ax_grid[0][1].hist(vals,bins=100, histtype='step', orientation='horizontal')

    plot_displacement( ax_grid[0][0], vals, label_obj, displacement_fn)
    plot_displacement( ax_grid[0][1], vals, label_obj, displacement_fn)
    return fig

def example_bonds():
    with open( 'oFF-1.1.0.p', 'rb') as fid:
        oFF = pickle.load(fid)
    with open( 'bonds.p', 'rb') as fid:
        bonds = pickle.load(fid)
    with open( 'QCA.p', 'rb') as fid:
        QCA = pickle.load(fid)
    if QCA.db is None:
        with open( 'QCA.db.p', 'rb') as fid:
            QCA.db = pickle.load(fid).db
    labels = list(oFF.db.get( "ROOT").get( "data").get( "Bonds").keys())

    def collect_and_plot( QCA, oFF, measurement, query, entry=None, verbose=False):
        ret = select_data_of_oFFlabel_from_td( QCA, oFF, bonds, query, entry=entry, verbose=False)
        if len(ret) == 0:
            return

        val = []
        [val.extend(x[5]) for x in ret]
        val = np.array(val)                                                                   
        
        ang = np.array( [x[4] for x in ret])                                                                                                         
        label_obj = oFF.db[ "ROOT"][ "data"][ "Bonds"][ q]                                                                          
        atoms = [(x[0], *x[3]) for x in ret]                                                                                                        
        fig = plot_td_minima( ang , val * const.bohr2angstrom, atoms, label_obj, molid=None, displacement_fn=bond_disp)                             
        if entry is None:
            figname = q + "." + "all" + ".min.png"
        else:
            figname = q + "." + entry.payload + ".min.png"
        fig.savefig( figname)
        plt.close('all')
        if entry is not None:
            print( "{:4s} {:3d} {:s}".format( q, len(val), QCA.db[ entry.payload][ 'entry'].name ))
        else:
            print( "{:4s} {:3d} {:s}".format( q, len(val), QCA.name))


    for q in labels:                                                                                                                                    
        collect_and_plot( QCA, oFF, bonds, q, entry=None, verbose=False)
        for entry in QCA.iter_entry():                                                                                                                  
            collect_and_plot( QCA, oFF, bonds, q, entry=entry, verbose=False)



if __name__ == "__main__":
    example_bonds()
