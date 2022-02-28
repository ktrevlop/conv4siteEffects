# conv4siteEffects
Konstantinos Trevlopoulos
Last update: 28.02.2021

This script implements the procedure described in the section "Convolution:
AF( f ) Dependent on Sra( f )" in Bazzurro and Cornell (2004).

https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/94/6/2110/147012/
Nonlinear-Soil-Site-Effects-in-Probabilistic

The script initially reads the hazard curves in a .hdf5 file created by the
OpenQuane Engine. Then it computes the new hazard curves through convolution.

The versions of the pieces of software that were used:
Spyder 3.3.6, Python 3.7.4 - IPython 7.8.0, OpenQuane Engine version 3.10,
h5py 2.9.0, numpy 1.16.5, scipy 1.3.1, pandas 0.25.1, glob2 0.7

DISCLAIMER

This software is made available as a prototype implementation  for the purpose
of open collaboration and in the hope that it will be useful. It is not
developed to design standards, nor subject to critical review by professional
software developers. It is therefore distributed WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE. See the GNU General Public License for more details:
https://www.gnu.org/licenses/gpl-3.0.html

The author of the software, assumes no liability for use of the software.
